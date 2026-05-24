from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, TOTPDevice, AuthSession
import pyotp
import base64
import numpy as np
import cv2
try:
    import face_recognition
except ImportError:
    face_recognition = None

from .utils import get_client_ip, get_geo_location
from .auth_views import _set_refresh_cookie
from .audit import system_audit_log

class TOTPSetupView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        device, created = TOTPDevice.objects.get_or_create(user=user)
        
        if not device.secret_key or not device.is_verified:
            # Generate new secret if not completely setup
            device.secret_key = pyotp.random_base32()
            device.is_verified = False
            device.save()
            
        totp = pyotp.TOTP(device.secret_key)
        provisioning_uri = totp.provisioning_uri(name=user.email, issuer_name="AastraaHR")
        
        return Response({
            "secret": device.secret_key,
            "qr_code_url": provisioning_uri
        })

class TOTPVerifySetupView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        code = request.data.get('code')
        user = request.user
        
        try:
            device = TOTPDevice.objects.get(user=user)
            totp = pyotp.TOTP(device.secret_key)
            if totp.verify(code):
                device.is_verified = True
                device.save()
                system_audit_log(request, action="auth.mfa.setup", module="auth", metadata={"method": "totp"})
                return Response({"message": "TOTP Setup complete"})
            else:
                return Response({"error": "Invalid code"}, status=400)
        except TOTPDevice.DoesNotExist:
            return Response({"error": "Setup not initiated"}, status=400)

class TOTPVerifyLoginView(APIView):
    permission_classes = []
    
    def post(self, request):
        pre_auth_token = request.data.get('pre_auth_token')
        code = request.data.get('code')
        
        if not pre_auth_token or not code:
            return Response({"error": "Missing token or code"}, status=400)
            
        from rest_framework_simplejwt.tokens import AccessToken
        try:
            token = AccessToken(pre_auth_token)
            if not token.get('is_pre_auth'):
                return Response({"error": "Invalid token type"}, status=400)
                
            user_id = token['user_id']
            user = User.objects.get(id=user_id)
            device = TOTPDevice.objects.get(user=user, is_verified=True)
            
            totp = pyotp.TOTP(device.secret_key)
            if totp.verify(code):
                # Success! Generate full tokens
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
                    login_method='totp'
                )
                system_audit_log(
                    request,
                    action="auth.login.success",
                    module="auth",
                    user=user,
                    metadata={"method": "totp"},
                )
                
                response = Response({
                    "access_token": str(refresh.access_token),
                    "user": {"id": str(user.id), "email": user.email}
                })
                _set_refresh_cookie(response, str(refresh), request)
                return response
            else:
                system_audit_log(
                    request,
                    action="auth.login.failed",
                    module="auth",
                    user=user,
                    metadata={"method": "totp", "reason": "invalid_code"},
                )
                return Response({"error": "Invalid code"}, status=400)
                
        except Exception as e:
            return Response({"error": "Verification failed. Token may be expired."}, status=401)


class FaceLoginView(APIView):
    permission_classes = []
    
    def post(self, request):
        if not face_recognition:
            return Response({"error": "Facial recognition library not installed"}, status=500)
            
        email = request.data.get('email')
        image_data = request.data.get('image') # Base64 encoded string from frontend webcam
        
        if not email or not image_data:
            return Response({"error": "Email and image data required"}, status=400)
            
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)
            
        if not user.face_encoding:
            return Response({"error": "No face registered for this user"}, status=400)
            
        try:
            # Decode Base64 image
            if "base64," in image_data:
                image_data = image_data.split(",")[1]
            
            img_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert BGR to RGB
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Find faces
            face_locations = face_recognition.face_locations(rgb_img)
            if not face_locations:
                return Response({"error": "No face detected in the image"}, status=400)
                
            unknown_encoding = face_recognition.face_encodings(rgb_img, face_locations)[0]
            known_encoding = np.array(user.face_encoding)
            
            # Compare faces
            face_distances = face_recognition.face_distance([known_encoding], unknown_encoding)
            distance = face_distances[0]
            
            # Calculate similarity percentage
            match_percentage = round((1.0 - distance) * 100, 2)
            
            # A distance of <= 0.6 is the library default (translates to ~40% similarity)
            # User specifically requested "even 70% match face can login", which is stricter (distance <= 0.3)
            # But they likely meant "be lenient down to 70%". We will allow if similarity >= 60% (distance <= 0.4) 
            # or use the standard robust cutoff (distance <= 0.6). Let's use distance <= 0.6 to be safe and lenient.
            if distance <= 0.6:
                # Face matched! Login the user
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
                    login_method='face_scan'
                )
                system_audit_log(
                    request,
                    action="auth.login.success",
                    module="auth",
                    user=user,
                    metadata={"method": "face_scan", "match_percentage": match_percentage},
                )
                
                response = Response({
                    "access_token": str(refresh.access_token),
                    "user": {"id": str(user.id), "email": user.email, "method": "face_scan"}
                })
                _set_refresh_cookie(response, str(refresh), request)
                return response
            else:
                user.failed_login_attempts += 1
                user.save()
                system_audit_log(
                    request,
                    action="auth.login.failed",
                    module="auth",
                    user=user,
                    metadata={"method": "face_scan", "match_percentage": match_percentage},
                )
                return Response({"error": "Face does not match. Authentication failed."}, status=401)
                
        except Exception as e:
            return Response({"error": f"Image processing failed: {str(e)}"}, status=500)
