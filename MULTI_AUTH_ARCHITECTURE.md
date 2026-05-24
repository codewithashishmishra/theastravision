# Enterprise Multi-Auth Architecture Blueprint

This document outlines the complete architectural design and code implementation for a secure, enterprise-grade multi-login authentication system using Django REST Framework (DRF) and Next.js.

## 1. Architecture Overview

### Backend (Django REST Framework + PostgreSQL)
*   **Token Strategy:** Short-lived JWT Access Tokens (15 mins) delivered in JSON payload. Long-lived Refresh Tokens (7 days) delivered exclusively via `HttpOnly`, `Secure`, `SameSite=Strict` cookies.
*   **Session & Auditing:** Every login generates an `AuthSession` and a `SystemAuditLog` entry tracking IP, Device Fingerprint, and Location.
*   **Rate Limiting:** Strict throttling on OTP generation, failed password attempts, and MPIN attempts using Redis.
*   **Cryptography:** Argon2id for password and MPIN hashing. HMAC for Magic Links. PyOTP for TOTP generation. WebAuthn for Passkeys/Face ID.

### Frontend (Next.js + Tailwind + React Hook Form + Zod)
*   **State Management:** React Context + Axios Interceptors for silent token refresh.
*   **Security:** No sensitive tokens in `localStorage`. Access tokens are kept in memory.
*   **UI/UX:** Modular `AuthCard` with dynamic `LoginMethodSelector` supporting Password, OTP, TOTP, and Passkey flows.

---

## 2. Database Schema (Django Models)

```python
# core/models.py
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_email_verified = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

class TOTPDevice(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    secret_key = models.CharField(max_length=255) # Encrypted at rest
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class RecoveryCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=255) # Hashed
    is_used = models.BooleanField(default=False)

class WebAuthnCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    credential_id = models.CharField(max_length=255, unique=True)
    public_key = models.TextField()
    sign_count = models.IntegerField(default=0)
    name = models.CharField(max_length=100) # e.g., "iPhone FaceID"

class MPINCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)
    mpin_hash = models.CharField(max_length=255) # Argon2 hash
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

class TrustedDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_fingerprint = models.CharField(max_length=255, unique=True)
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    last_used_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

class AuthSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    refresh_token_jti = models.UUIDField(unique=True)
    device_fingerprint = models.CharField(max_length=255, null=True)
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## 3. Backend APIs (Django REST Framework)

### `urls.py` Structure
```python
from django.urls import path
from .views import auth_views, mfa_views, passkey_views

urlpatterns = [
    # Core Auth
    path('auth/login/password/', auth_views.LoginPasswordView.as_view()),
    path('auth/login/email-otp/request/', auth_views.RequestOTPView.as_view()),
    path('auth/login/email-otp/verify/', auth_views.VerifyOTPView.as_view()),
    path('auth/token/refresh/', auth_views.RefreshTokenView.as_view()),
    path('auth/logout/', auth_views.LogoutView.as_view()),
    
    # TOTP
    path('auth/totp/setup/', mfa_views.TOTPSetupView.as_view()),
    path('auth/totp/verify-setup/', mfa_views.TOTPVerifySetupView.as_view()),
    path('auth/totp/verify-login/', mfa_views.TOTPVerifyLoginView.as_view()),
    
    # WebAuthn (FaceID/Passkeys)
    path('auth/passkey/register/options/', passkey_views.PasskeyRegisterOptions.as_view()),
    path('auth/passkey/register/verify/', passkey_views.PasskeyRegisterVerify.as_view()),
    path('auth/passkey/login/options/', passkey_views.PasskeyLoginOptions.as_view()),
    path('auth/passkey/login/verify/', passkey_views.PasskeyLoginVerify.as_view()),
]
```

### Password Login Implementation (with Brute Force Protection)
```python
# core/views/auth_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.tokens import RefreshToken

class LoginPasswordView(APIView):
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        user = User.objects.filter(email=email).first()
        if not user:
            # Prevent email enumeration
            return Response({"error": "Invalid credentials"}, status=401)
            
        if user.locked_until and user.locked_until > timezone.now():
            return Response({"error": "Account temporarily locked."}, status=423)

        authenticated_user = authenticate(username=email, password=password)
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
            # Issue a temporary 'pre-auth' token instead of full access
            pre_auth_token = generate_pre_auth_token(user.id)
            return Response({"requires_totp": True, "pre_auth_token": pre_auth_token})

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        response = Response({
            "access_token": str(refresh.access_token),
            "user": {"id": user.id, "email": user.email}
        })
        
        # Set HttpOnly Cookie for Refresh Token
        response.set_cookie(
            key='refresh_token', 
            value=str(refresh), 
            httponly=True, 
            secure=True, 
            samesite='Strict'
        )
        return response
```

---

## 4. Frontend Next.js Architecture

### Zod Validation Schemas
```typescript
// src/lib/validations/auth.ts
import { z } from "zod";

export const LoginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export const TOTPSchema = z.object({
  code: z.string().length(6, "Code must be exactly 6 digits").regex(/^\d+$/, "Must be numbers only"),
});
```

### Axios Interceptor for Silent Refresh
```typescript
// src/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // Crucial for sending the HttpOnly refresh token cookie
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // The browser automatically sends the HttpOnly cookie here
        const res = await axios.post('/api/v1/auth/token/refresh/', {}, { withCredentials: true });
        
        // Update in-memory access token
        const newAccessToken = res.data.access_token;
        api.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
        
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, force logout
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);
export default api;
```

### Modular Login Component (React)
```tsx
// src/components/auth/MultiLogin.tsx
'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoginSchema } from '@/lib/validations/auth';
import api from '@/lib/api';
import { Fingerprint, Mail, KeyRound } from 'lucide-react';

export default function MultiLogin() {
  const [step, setStep] = useState<'CREDENTIALS' | 'TOTP'>('CREDENTIALS');
  const [preAuthToken, setPreAuthToken] = useState('');

  const form = useForm({ resolver: zodResolver(LoginSchema) });

  const handlePasswordLogin = async (data: any) => {
    try {
      const res = await api.post('/auth/login/password/', data);
      
      if (res.data.requires_totp) {
        setPreAuthToken(res.data.pre_auth_token);
        setStep('TOTP');
      } else {
        // Success, redirect to dash
        window.location.href = '/dashboard';
      }
    } catch (err) {
      // Handle error (show toast)
    }
  };

  const handlePasskeyLogin = async () => {
    // 1. Fetch challenge from /auth/passkey/login/options/
    // 2. Call navigator.credentials.get()
    // 3. Send assertion to /auth/passkey/login/verify/
  };

  return (
    <div className="w-full max-w-md mx-auto p-6 bg-white dark:bg-gray-900 rounded-2xl shadow-xl">
      {step === 'CREDENTIALS' && (
        <form onSubmit={form.handleSubmit(handlePasswordLogin)} className="space-y-4">
          <input {...form.register('email')} placeholder="Email" className="w-full p-3 border rounded-lg" />
          <input type="password" {...form.register('password')} placeholder="Password" className="w-full p-3 border rounded-lg" />
          <button type="submit" className="w-full bg-blue-600 text-white p-3 rounded-lg font-bold">Sign In</button>
          
          <div className="my-4 flex items-center gap-2">
            <hr className="flex-1" /><span className="text-sm text-gray-500">OR</span><hr className="flex-1" />
          </div>

          <button type="button" onClick={handlePasskeyLogin} className="w-full flex items-center justify-center gap-2 border p-3 rounded-lg hover:bg-gray-50">
            <Fingerprint size={20} /> Sign in with Passkey / Face ID
          </button>
        </form>
      )}

      {step === 'TOTP' && (
        <div className="space-y-4 text-center">
          <h3 className="font-bold text-xl">Two-Factor Authentication</h3>
          <p className="text-gray-500 text-sm">Enter the 6-digit code from your Authenticator app.</p>
          <input type="text" maxLength={6} className="w-full p-3 border rounded-lg text-center tracking-[0.5em] text-2xl" />
          <button className="w-full bg-blue-600 text-white p-3 rounded-lg font-bold">Verify Code</button>
        </div>
      )}
    </div>
  );
}
```

---

## 5. Security Best Practices Implemented
1. **No LocalStorage for Refresh Tokens:** Prevents Cross-Site Scripting (XSS) from exfiltrating the long-lived refresh token.
2. **Pre-Auth Tokens for MFA:** Prevents a user from accessing the system if they pass password validation but fail TOTP. The initial API returns a tightly scoped, 5-minute JWT (`pre_auth_token`) that is ONLY valid for the `/totp/verify-login/` endpoint.
3. **Email Enumeration Prevention:** Returning "Invalid Credentials" generically instead of "User not found" or "Incorrect password" prevents attackers from mapping valid email addresses.
4. **Biometric Data:** Following FIDO2 WebAuthn standards. The server NEVER sees fingerprints or face data; it only stores a cryptographic Public Key. Verification is purely challenge-response based.
