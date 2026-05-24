'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Card, CardBody, CardHeader, Input, Button, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter } from '@nextui-org/react';
import { Mail, Lock, Fingerprint, ShieldCheck, ShieldAlert, Camera, ScanFace } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { api } from '@/lib/api';
import { buildTrackerCallbackUrl, isAllowedTrackerRedirect } from '@/lib/trackerRedirect';
import { startAuthentication } from '@simplewebauthn/browser';
import { loadAndPersistAuthSession } from '@/lib/authSession';
import AppFooter from '@/components/layouts/AppFooter';

export default function MultiLogin() {
  const [step, setStep] = useState<'CREDENTIALS' | 'TOTP' | 'FACE_SCAN'>('CREDENTIALS');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [preAuthToken, setPreAuthToken] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isPasskeyModalOpen, setIsPasskeyModalOpen] = useState(false);
  
  // Webcam Face Scan State
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);

  const router = useRouter();
  const searchParams = useSearchParams();
  const trackerRedirect = searchParams.get('tracker_redirect');
  const trackerState = searchParams.get('state');
  const isTrackerLogin = Boolean(trackerRedirect && isAllowedTrackerRedirect(trackerRedirect));

  const persistTokens = (accessToken: string, refreshToken?: string) => {
    localStorage.setItem('access_token', accessToken);
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken);
    }
  };

  const finishAuth = (accessToken: string, refreshToken?: string, email?: string) => {
    if (trackerRedirect && isAllowedTrackerRedirect(trackerRedirect)) {
      window.location.href = buildTrackerCallbackUrl(trackerRedirect, {
        access_token: accessToken,
        refresh_token: refreshToken,
        state: trackerState || undefined,
        email,
      });
      return true;
    }
    return false;
  };

  const handleAuthSuccess = async (accessToken: string, refreshToken?: string, email?: string) => {
    if (finishAuth(accessToken, refreshToken, email)) return;
    persistTokens(accessToken, refreshToken);
    setIsLoading(true);
    setError('');
    try {
      const { homeRoute } = await loadAndPersistAuthSession();
      router.push(homeRoute);
    } catch {
      setError('Signed in but could not load your profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const res = await api.post('/auth/login/password/', { email, password });
      if (res.data.requires_totp) {
        setPreAuthToken(res.data.pre_auth_token);
        setStep('TOTP');
      } else if (res.data.access_token) {
        await handleAuthSuccess(res.data.access_token, res.data.refresh_token, email);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Invalid credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTotpVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const res = await api.post('/auth/totp/verify-login/', { pre_auth_token: preAuthToken, code: totpCode });
      if (res.data.access_token) {
        await handleAuthSuccess(res.data.access_token, res.data.refresh_token, email);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Invalid TOTP code.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasskeyLogin = async () => {
    setIsPasskeyModalOpen(true);
    setError('');
    try {
      // 1. Get Authentication Options from Backend
      const optionsRes = await api.post('/auth/passkey/login/options/');
      const options = optionsRes.data;

      // 2. Prompt Browser for FaceID/TouchID/YubiKey
      const asseResp = await startAuthentication(options);

      // 3. Send Assertion back to verify
      const verificationRes = await api.post('/auth/passkey/login/verify/', asseResp);
      
      if (verificationRes.data.access_token) {
        setIsPasskeyModalOpen(false);
        await handleAuthSuccess(
          verificationRes.data.access_token,
          verificationRes.data.refresh_token,
          verificationRes.data.user?.email
        );
      }
    } catch (err: any) {
      setError('Biometric/Passkey Authentication Failed. ' + (err.message || ''));
      setIsPasskeyModalOpen(false);
    }
  };

  const startWebcam = async () => {
    if (!email) {
      setError("Please enter your email first to use Face Login.");
      return;
    }
    setError('');
    setStep('FACE_SCAN');
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      setError("Webcam access denied or unavailable.");
      setStep('CREDENTIALS');
    }
  };

  const stopWebcam = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  }, [stream]);

  const captureAndVerifyFace = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    setIsLoading(true);
    setError('');
    const context = canvasRef.current.getContext('2d');
    if (context) {
      canvasRef.current.width = videoRef.current.videoWidth;
      canvasRef.current.height = videoRef.current.videoHeight;
      context.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);
      const base64Image = canvasRef.current.toDataURL('image/jpeg');

      try {
        const res = await api.post('/auth/face/login/', { email, image: base64Image });
        if (res.data.access_token) {
          stopWebcam();
          await handleAuthSuccess(
            res.data.access_token,
            res.data.refresh_token,
            res.data.user?.email
          );
        }
      } catch (err: any) {
        setError(err.response?.data?.error || 'Facial Recognition Failed. Face does not match.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative overflow-hidden">
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/20 blur-[120px] rounded-full z-0 pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-secondary/20 blur-[120px] rounded-full z-0 pointer-events-none" />

      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.5 }} className="w-full max-w-md z-10">
        <Card className="w-full shadow-2xl bg-content1/80 backdrop-blur-xl border border-divider">
          
          <CardHeader className="flex flex-col gap-3 items-center pt-10 pb-2">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-2 shadow-inner border ${step === 'TOTP' ? 'bg-warning/10 text-warning border-warning/20' : step === 'FACE_SCAN' ? 'bg-success/10 text-success border-success/20' : 'bg-primary/10 text-primary border-primary/20'}`}>
              {step === 'TOTP' ? <ShieldAlert size={32} /> : step === 'FACE_SCAN' ? <ScanFace size={32} /> : <ShieldCheck size={32} />}
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">
              {isTrackerLogin
                ? 'Sign in to WFH Tracker'
                : step === 'TOTP'
                  ? 'Two-Factor Auth'
                  : step === 'FACE_SCAN'
                    ? 'Face Scan Login'
                    : 'Welcome Back'}
            </h1>
            <p className="text-default-500 text-sm">
              {isTrackerLogin
                ? 'Use your HRMS credentials — you will return to the desktop app automatically.'
                : step === 'TOTP'
                  ? 'Enter your 6-digit Authenticator Code'
                  : step === 'FACE_SCAN'
                    ? 'Look directly at the camera'
                    : 'Sign in to AastraaHR Enterprise'}
            </p>
          </CardHeader>
          
          <CardBody className="px-10 py-8">
            {error && (
              <div className="p-3 mb-6 bg-danger/10 border border-danger/20 rounded-xl text-danger text-sm font-medium text-center animate-appearance-in">
                {error}
              </div>
            )}

            {step === 'CREDENTIALS' && (
              <form onSubmit={handlePasswordLogin} className="flex flex-col gap-4">
                <Input type="email" label="Email / Username" variant="bordered" startContent={<Mail size={18} className="text-default-400" />} value={email} onValueChange={setEmail} isRequired classNames={{inputWrapper: "h-14"}} />
                <Input type="password" label="Password" variant="bordered" startContent={<Lock size={18} className="text-default-400" />} value={password} onValueChange={setPassword} classNames={{inputWrapper: "h-14"}} />
                
                <Button type="submit" color="primary" size="lg" className="w-full font-bold shadow-lg shadow-primary/30 mt-2 h-14" isLoading={isLoading}>
                  Sign in with Password
                </Button>

                <div className="my-2 flex items-center gap-4">
                  <div className="h-px bg-divider flex-1"></div>
                  <span className="text-xs text-default-400 font-bold uppercase tracking-widest">or</span>
                  <div className="h-px bg-divider flex-1"></div>
                </div>

                <div className="flex gap-2">
                  <Button type="button" variant="flat" color="secondary" size="lg" className="flex-1 font-bold h-14" onPress={handlePasskeyLogin} startContent={<Fingerprint size={20} />}>
                    Passkey / FIDO2
                  </Button>
                  <Button type="button" variant="flat" color="success" size="lg" className="flex-1 font-bold h-14" onPress={startWebcam} startContent={<Camera size={20} />}>
                    Face Scan
                  </Button>
                </div>
              </form>
            )}

            {step === 'TOTP' && (
              <form onSubmit={handleTotpVerify} className="flex flex-col gap-6">
                <Input type="text" maxLength={6} label="TOTP Code" variant="bordered" value={totpCode} onValueChange={setTotpCode} isRequired classNames={{inputWrapper: "h-14", input: "text-center tracking-[0.5em] text-2xl font-mono"}} />
                <Button type="submit" color="warning" size="lg" className="w-full font-bold shadow-lg shadow-warning/30 mt-2 h-14" isLoading={isLoading}>
                  Verify & Sign In
                </Button>
                <Button variant="light" className="text-default-500 font-medium" onPress={() => setStep('CREDENTIALS')}>
                  Cancel
                </Button>
              </form>
            )}

            {step === 'FACE_SCAN' && (
              <div className="flex flex-col gap-6 items-center">
                <div className="w-full relative rounded-2xl overflow-hidden border-2 border-primary/50 shadow-xl aspect-square bg-black">
                  <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover transform -scale-x-100" />
                  <div className="absolute inset-0 pointer-events-none border-[4px] border-primary/20 rounded-2xl"></div>
                  {/* Scanning Guide Overlay */}
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="w-48 h-64 border-2 border-dashed border-primary/50 rounded-[40%] animate-pulse"></div>
                  </div>
                </div>
                <canvas ref={canvasRef} className="hidden" />
                
                <Button color="success" size="lg" className="w-full font-bold shadow-lg shadow-success/30 h-14" isLoading={isLoading} onPress={captureAndVerifyFace}>
                  Scan Face & Login
                </Button>
                <Button variant="light" className="text-default-500 font-medium w-full" onPress={() => { stopWebcam(); setStep('CREDENTIALS'); }}>
                  Cancel
                </Button>
              </div>
            )}

          </CardBody>
        </Card>
      </motion.div>

      <Modal isOpen={isPasskeyModalOpen} onOpenChange={setIsPasskeyModalOpen} backdrop="blur">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">Passkey / Pendrive Auth</ModalHeader>
              <ModalBody className="flex flex-col items-center justify-center py-8 text-center">
                <div className="w-20 h-20 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-4 animate-pulse">
                  <Fingerprint size={40} />
                </div>
                <h3 className="text-xl font-bold">Awaiting Security Key</h3>
                <p className="text-default-500 text-sm max-w-xs mt-2">
                  Please use your device's Touch ID, Face ID, or insert your USB Security Key (YubiKey) to authenticate via FIDO2 WebAuthn protocol.
                </p>
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="light" onPress={onClose}>
                  Cancel
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

      <AppFooter className="w-full max-w-md z-10 border-none mt-6" />
    </div>
  );
}
