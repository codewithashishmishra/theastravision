from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.throttling import AnonRateThrottle
from .models import User, AuthSession, UserRoleMapping
import uuid
from .utils import get_client_ip, get_geo_location


def _get_refresh_token_from_request(request):
    body = request.data.get('refresh') if hasattr(request, 'data') else None
    return body or request.COOKIES.get('refresh_token')


def _set_refresh_cookie(response, refresh_token_str, request):
    response.set_cookie(
        key='refresh_token',
        value=refresh_token_str,
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Strict',
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


def serialize_auth_me(user):
    roles = get_user_role_names(user)
    tenant_payload = None
    if user.tenant_id:
        tenant = user.tenant
        tenant_payload = {
            'id': str(tenant.id),
            'name': tenant.name,
            'email_domain': tenant.email_domain or '',
        }
    display_name = (user.get_full_name() or '').strip() or user.email
    return {
        'email': user.email,
        'display_name': display_name,
        'roles': roles,
        'tenant': tenant_payload,
    }

class LoginRateThrottle(AnonRateThrottle):
    rate = '10/min'

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
            return Response({"error": "Invalid credentials"}, status=401)
            
        if user.locked_until and user.locked_until > timezone.now():
            return Response({"error": "Account temporarily locked. Try again later."}, status=423)

        # In Django, authenticate usually expects 'username' instead of 'email' unless configured otherwise
        authenticated_user = authenticate(username=user.username, password=password)
        
        if not authenticated_user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = timezone.now() + timedelta(minutes=15)
            user.save()
            return Response({"error": "Invalid credentials"}, status=401)
            
        # Reset attempts on success
        user.failed_login_attempts = 0
        user.locked_until = None
        user.save()

        # Check if TOTP is enabled
        if hasattr(user, 'totpdevice') and user.totpdevice.is_verified:
            pre_auth_token = generate_pre_auth_token(user.id)
            return Response({"requires_totp": True, "pre_auth_token": pre_auth_token})

        # Generate Full Tokens
        ip = get_client_ip(request)
        city, country = get_geo_location(ip)
        refresh = RefreshToken.for_user(user)
        
        # Log the session
        AuthSession.objects.create(
            user=user,
            refresh_token_jti=refresh['jti'],
            device_fingerprint=request.META.get('HTTP_USER_AGENT', 'Unknown'),
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
            location_city=city,
            location_country=country,
            login_method='password',
            client_type='web',
        )
        
        response = Response({
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        })
        
        _set_refresh_cookie(response, str(refresh), request)
        return response

class RefreshTokenView(APIView):
    permission_classes = []
    
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
        return Response(serialize_auth_me(request.user))


class LogoutView(APIView):
    def post(self, request):
        refresh_token = _get_refresh_token_from_request(request)
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                session = AuthSession.objects.filter(refresh_token_jti=token['jti']).first()
                if session:
                    session.is_revoked = True
                    session.save()
            except Exception:
                pass
                
        response = Response({"message": "Logged out successfully"})
        response.delete_cookie('refresh_token')
        return response
