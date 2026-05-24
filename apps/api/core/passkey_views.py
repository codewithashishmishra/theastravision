from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from webauthn import generate_registration_options, verify_registration_response, generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import RegistrationCredential, AuthenticationCredential, AuthenticatorSelectionCriteria, UserVerificationRequirement
from webauthn.helpers import options_to_json
from .models import WebAuthnCredential, User, AuthSession
from rest_framework_simplejwt.tokens import RefreshToken
import os
import json
from .utils import get_client_ip, get_geo_location
from .auth_views import _set_refresh_cookie
from .audit import system_audit_log

RP_ID = "localhost"
RP_NAME = "AastraaHR Enterprise"
ORIGIN = "http://localhost:3000"

class PasskeyRegisterOptions(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Existing credentials to prevent re-registration
        existing_creds = WebAuthnCredential.objects.filter(user=user)
        exclude_credentials = [{"id": cred.credential_id, "type": "public-key"} for cred in existing_creds]
        
        options = generate_registration_options(
            rp_id=RP_ID,
            rp_name=RP_NAME,
            user_id=str(user.id).encode(),
            user_name=user.email,
            exclude_credentials=exclude_credentials,
            authenticator_selection=AuthenticatorSelectionCriteria(
                user_verification=UserVerificationRequirement.PREFERRED
            )
        )
        
        # Store challenge in session (In real prod, store in Redis/Cache)
        request.session['webauthn_registration_challenge'] = options.challenge
        
        return Response(json.loads(options_to_json(options)))


class PasskeyRegisterVerify(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        challenge = request.session.get('webauthn_registration_challenge')
        
        if not challenge:
            return Response({"error": "Challenge missing"}, status=400)
            
        try:
            credential = RegistrationCredential.parse_raw(json.dumps(request.data))
            verification = verify_registration_response(
                credential=credential,
                expected_challenge=challenge,
                expected_rp_id=RP_ID,
                expected_origin=ORIGIN
            )
            
            # Store public key in DB
            WebAuthnCredential.objects.create(
                user=user,
                credential_id=verification.credential_id.hex(),
                public_key=verification.credential_public_key,
                sign_count=verification.sign_count,
                name="Passkey Authenticator"
            )
            system_audit_log(request, action="auth.passkey.register", module="auth")
            
            return Response({"message": "Passkey registered successfully"})
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class PasskeyLoginOptions(APIView):
    permission_classes = []
    
    def post(self, request):
        # We don't specify user for a pure passkey login (let the authenticator identify the user)
        options = generate_authentication_options(
            rp_id=RP_ID,
            user_verification=UserVerificationRequirement.PREFERRED
        )
        
        # Store challenge temporarily (We will use django sessions)
        request.session['webauthn_login_challenge'] = options.challenge
        
        return Response(json.loads(options_to_json(options)))


class PasskeyLoginVerify(APIView):
    permission_classes = []
    
    def post(self, request):
        challenge = request.session.get('webauthn_login_challenge')
        if not challenge:
            return Response({"error": "Challenge missing"}, status=400)
            
        try:
            credential = AuthenticationCredential.parse_raw(json.dumps(request.data))
            
            # Look up the public key by credential ID
            cred_id_hex = credential.id
            webauthn_cred = WebAuthnCredential.objects.filter(credential_id=cred_id_hex).first()
            
            if not webauthn_cred:
                return Response({"error": "Credential not found"}, status=404)
                
            verification = verify_authentication_response(
                credential=credential,
                expected_challenge=challenge,
                expected_rp_id=RP_ID,
                expected_origin=ORIGIN,
                credential_public_key=webauthn_cred.public_key,
                credential_current_sign_count=webauthn_cred.sign_count
            )
            
            # Update sign count
            webauthn_cred.sign_count = verification.new_sign_count
            webauthn_cred.save()
            
            # Login successful
            user = webauthn_cred.user
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save()
            
            ip = get_client_ip(request)
            city, country = get_geo_location(ip)
            refresh = RefreshToken.for_user(user)
            AuthSession.objects.create(
                user=user,
                refresh_token_jti=refresh['jti'],
                device_fingerprint=request.META.get('HTTP_USER_AGENT', 'Unknown'),
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
                location_city=city,
                location_country=country,
                login_method='passkey'
            )
            system_audit_log(
                request,
                action="auth.login.success",
                module="auth",
                user=user,
                metadata={"method": "passkey"},
            )
            
            response = Response({
                "access_token": str(refresh.access_token),
                "user": {"id": str(user.id), "email": user.email, "method": "passkey"}
            })
            _set_refresh_cookie(response, str(refresh), request)
            return response
            
        except Exception as e:
            return Response({"error": str(e)}, status=400)
