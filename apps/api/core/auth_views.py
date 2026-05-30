from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework.throttling import AnonRateThrottle
from .models import User, AuthSession, UserRoleMapping
from .auth_utils import mfa_setup_required_response, user_has_verified_mfa, user_requires_mfa
import uuid
from .utils import get_client_ip, get_geo_location
from .audit import system_audit_log
from .timezone_utils import resolve_viewing_timezone
from core.e2ee.services import bind_session_to_auth, delete_session, load_session_aes_key, wrap_auth_session_key


def _get_refresh_token_from_request(request):
    body = request.data.get('refresh') if hasattr(request, 'data') else None
    return body or request.COOKIES.get('refresh_token')


def _set_refresh_cookie(response, refresh_token_str, request):
    response.set_cookie(
        key='refresh_token',
        value=refresh_token_str,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax' if settings.DEBUG else 'Strict',
    )
    return response


def _access_token_payload(access_str):
    return {'access': access_str, 'access_token': access_str}


def get_user_role_names(user):
    if user.is_superuser:
        return ['Super Admin']
    return list(
        UserRoleMapping.objects.filter(user=user)
        .select_related('role')
        .values_list('role__name', flat=True)
        .distinct()
    )


def serialize_auth_me(user, request=None):
    roles = get_user_role_names(user)
    tenant_payload = None
    if user.tenant_id:
        tenant = user.tenant
        tenant_payload = {
            'id': str(tenant.id),
            'name': tenant.name,
            'email_domain': tenant.email_domain or '',
            'enabled_jurisdictions': tenant.enabled_jurisdictions or ['IN'],
            'default_currency': tenant.default_currency or 'INR',
            'subscription_plan': tenant.subscription_plan or 'starter',
        }
    display_name = (user.get_full_name() or '').strip() or user.email
    viewing_timezone = str(resolve_viewing_timezone(request, user=user)) if request else None
    payload = {
        'email': user.email,
        'display_name': display_name,
        'roles': roles,
        'tenant': tenant_payload,
    }
    if viewing_timezone:
        payload['viewing_timezone'] = viewing_timezone
    return payload

class LoginRateThrottle(AnonRateThrottle):
    scope = 'auth_login'


class RefreshRateThrottle(AnonRateThrottle):
    scope = 'auth_refresh'


def _blacklist_token_jti(jti, user=None):
    outstanding, _ = OutstandingToken.objects.get_or_create(
        jti=jti,
        defaults={
            'user': user,
            'token': '',
            'created_at': timezone.now(),
            'expires_at': timezone.now() + timedelta(days=1),
        },
    )
    if user and outstanding.user_id is None:
        outstanding.user = user
        outstanding.save(update_fields=['user'])
    BlacklistedToken.objects.get_or_create(token=outstanding)


def _blacklist_request_access_token(request, user=None):
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Bearer '):
        return
    try:
        access = AccessToken(auth_header.split(' ', 1)[1])
        _blacklist_token_jti(access['jti'], user=user)
    except Exception:
        pass


def _issue_login_response(request, user, login_method='password', client_type='web'):
    if user_requires_mfa(user) and not user_has_verified_mfa(user):
        system_audit_log(
            request,
            action="auth.login.blocked",
            module="auth",
            user=user,
            metadata={"reason": "mfa_setup_required"},
        )
        return mfa_setup_required_response()

    ip = get_client_ip(request)
    city, country = get_geo_location(ip)
    refresh = RefreshToken.for_user(user)

    auth_session = AuthSession.objects.create(
        user=user,
        refresh_token_jti=refresh['jti'],
        device_fingerprint=request.META.get('HTTP_USER_AGENT', 'Unknown'),
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
        location_city=city,
        location_country=country,
        login_method=login_method,
        client_type=client_type,
    )

    client_ecdh = (
        (request.data.get('client_ecdh_public') if hasattr(request, 'data') else None)
        or request.META.get('HTTP_X_CLIENT_ECDH_PUBLIC', '').strip()
        or None
    )
    e2ee_session_id = (
        request.META.get('HTTP_X_E2EE_SESSION', '').strip()
        or (request.data.get('e2ee_session_id') or '').strip()
        or None
    )
    e2ee_meta = bind_session_to_auth(
        e2ee_session_id,
        client_ecdh,
        user_id=str(user.id),
        refresh_jti=str(refresh['jti']),
        client_type=client_type,
    )
    if e2ee_meta:
        sid = e2ee_meta.get('e2ee_session_id') or e2ee_session_id
        loaded = load_session_aes_key(sid) if sid else None
        if loaded:
            aes_key, _ = loaded
            auth_session.payload_key_wrapped = wrap_auth_session_key(aes_key)
            auth_session.save(update_fields=['payload_key_wrapped'])

    system_audit_log(
        request,
        action="auth.login.success",
        module="auth",
        user=user,
        metadata={"method": login_method, "client_type": client_type},
    )

    response = Response({
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        **(e2ee_meta or {}),
    })
    _set_refresh_cookie(response, str(refresh), request)
    return response

def generate_pre_auth_token(user_id):
    # For Phase 5 we use a highly restricted temporary token.
    # We will encode it manually or use SimpleJWT.
    from rest_framework_simplejwt.tokens import AccessToken
    token = AccessToken()
    token['user_id'] = str(user_id)
    token['is_pre_auth'] = True
    token.set_exp(lifetime=timedelta(minutes=5))
    return str(token)

class LoginPasswordView(APIView):
    throttle_classes = [LoginRateThrottle]
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = User.objects.filter(email=email).first()
        if not user:
            # Prevent email enumeration
            system_audit_log(
                request,
                action="auth.login.failed",
                module="auth",
                metadata={"email": email, "reason": "unknown_user"},
            )
            return Response({"error": "Invalid credentials"}, status=401)
            
        if user.locked_until and user.locked_until > timezone.now():
            system_audit_log(
                request,
                action="auth.login.blocked",
                module="auth",
                user=user,
                metadata={"reason": "account_locked"},
            )
            return Response({"error": "Account temporarily locked. Try again later."}, status=423)

        # In Django, authenticate usually expects 'username' instead of 'email' unless configured otherwise
        authenticated_user = authenticate(username=user.username, password=password)
        
        if not authenticated_user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = timezone.now() + timedelta(minutes=15)
            user.save()
            system_audit_log(
                request,
                action="auth.login.failed",
                module="auth",
                user=user,
                metadata={"email": email, "attempts": user.failed_login_attempts},
            )
            return Response({"error": "Invalid credentials"}, status=401)
            
        # Reset attempts on success
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()

        # Check if TOTP is enabled
        if hasattr(user, 'totpdevice') and user.totpdevice.is_verified:
            pre_auth_token = generate_pre_auth_token(user.id)
            return Response({"requires_totp": True, "pre_auth_token": pre_auth_token})

        return _issue_login_response(request, user)

class RefreshTokenView(APIView):
    permission_classes = []
    throttle_classes = [RefreshRateThrottle]
    
    def post(self, request):
        refresh_token = _get_refresh_token_from_request(request)
        if not refresh_token:
            return Response({"error": "No refresh token provided"}, status=401)
            
        try:
            token = RefreshToken(refresh_token)
            session = AuthSession.objects.filter(refresh_token_jti=token['jti']).first()
            if not session or session.is_revoked:
                return Response({"error": "Session revoked"}, status=401)

            access_str = str(token.access_token)
            response = Response(_access_token_payload(access_str))
            _set_refresh_cookie(response, str(token), request)
            return response
        except Exception as e:
            return Response({"error": str(e)}, status=401)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(serialize_auth_me(request.user, request=request))

    def patch(self, request):
        display_name = request.data.get('display_name')
        if display_name is not None:
            request.user.display_name = str(display_name).strip()[:255]
            request.user.save(update_fields=['display_name'])
        return Response(serialize_auth_me(request.user, request=request))


class LogoutView(APIView):
    def post(self, request):
        actor = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
        refresh_token = _get_refresh_token_from_request(request)
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                session = AuthSession.objects.filter(refresh_token_jti=token['jti']).first()
                if session:
                    actor = session.user
                    session.is_revoked = True
                    session.save()
                token.blacklist()
                system_audit_log(
                    request,
                    action="auth.logout",
                    module="auth",
                    user=actor,
                )
            except Exception:
                pass

        _blacklist_request_access_token(request, user=actor)

        delete_session(request.META.get('HTTP_X_E2EE_SESSION', '').strip() or None)

        response = Response({"message": "Logged out successfully"})
        response.delete_cookie('refresh_token')
        return response
