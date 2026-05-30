'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardBody, Button, Chip, Spinner } from '@nextui-org/react';
import { MapPin, Clock, LogIn, LogOut, Camera } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { attendanceApi, unwrapList } from '@/lib/hrmsApi';

type AttendanceLog = {
  id: string;
  date?: string;
  check_in?: string | null;
  check_out?: string | null;
};

function punchErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const d = err.response?.data;
    if (typeof d === 'object' && d) {
      if ('detail' in d && typeof d.detail === 'string') return d.detail;
      if ('error' in d && typeof d.error === 'string') return d.error;
      const fieldMsgs = Object.values(d as Record<string, unknown>)
        .flatMap((v) => (Array.isArray(v) ? v : [v]))
        .filter((x) => typeof x === 'string');
      if (fieldMsgs.length) return fieldMsgs.join(' ');
    }
    if (err.response?.status === 403) return 'No employee profile linked to your account. Ask HR to link your user.';
    if (err.response?.status === 422) return 'Selfie or GPS validation failed. Enable location and capture a selfie if required.';
  }
  return 'Punch failed. Check GPS, selfie, and try again.';
}

export default function WebCheckInPage() {
  const [time, setTime] = useState(new Date());
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [locError, setLocError] = useState('');
  const [selfieBlob, setSelfieBlob] = useState<Blob | null>(null);
  const [selfiePreviewUrl, setSelfiePreviewUrl] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [punchError, setPunchError] = useState('');
  const [trackingActive, setTrackingActive] = useState(false);
  const [trackingIntervalMinutes, setTrackingIntervalMinutes] = useState(10);
  const queryClient = useQueryClient();

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!selfieBlob) {
      setSelfiePreviewUrl(null);
      return;
    }
    const url = URL.createObjectURL(selfieBlob);
    setSelfiePreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [selfieBlob]);

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocError('Geolocation not supported');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocError('');
      },
      () => setLocError('Unable to get location — enable GPS permissions'),
      { enableHighAccuracy: true },
    );
  }, []);

  const { data: logsData, isLoading } = useQuery({
    queryKey: ['my-attendance-logs'],
    queryFn: async () => {
      const res = await attendanceApi.logs.list({ mine: '1' });
      return unwrapList<AttendanceLog>(res.data);
    },
  });

  const todayLog = logsData?.[0];
  const isCheckedIn = todayLog?.check_in && !todayLog?.check_out;

  const punchMutation = useMutation({
    mutationFn: async (type: 'in' | 'out') => {
      if (!location) {
        throw new Error('GPS location is required before punching. Enable location access and wait for coordinates.');
      }
      const fd = new FormData();
      fd.append('lat', String(location.lat));
      fd.append('lng', String(location.lng));
      if (selfieBlob) fd.append('selfie', selfieBlob, 'selfie.jpg');
      if (type === 'in') return attendanceApi.logs.punchIn(fd);
      return attendanceApi.logs.punchOut(fd);
    },
    onSuccess: (resp, type) => {
      queryClient.invalidateQueries({ queryKey: ['my-attendance-logs'] });
      setSelfieBlob(null);
      setCameraOn(false);
      setPunchError('');
      const payload = (resp as { data?: { tracking_active?: boolean; interval_minutes?: number } })?.data ?? {};
      if (type === 'in' && payload.tracking_active) {
        setTrackingActive(true);
        setTrackingIntervalMinutes(payload.interval_minutes || 10);
      }
      if (type === 'out') setTrackingActive(false);
    },
    onError: (err) => {
      setPunchError(punchErrorMessage(err));
    },
  });

  const fieldPingMutation = useMutation({
    mutationFn: () => {
      if (!location) return Promise.resolve(null);
      return attendanceApi.fieldPings.create({
        latitude: location.lat,
        longitude: location.lng,
        source: 'Web',
      });
    },
  });

  useEffect(() => {
    if (!trackingActive || !isCheckedIn) return;
    const id = setInterval(() => {
      if (!navigator.geolocation) return;
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const next = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          setLocation(next);
          fieldPingMutation.mutate();
        },
        () => undefined,
        { enableHighAccuracy: true },
      );
    }, Math.max(5, trackingIntervalMinutes) * 60 * 1000);
    return () => clearInterval(id);
  }, [trackingActive, trackingIntervalMinutes, isCheckedIn]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraOn(true);
        setSelfieBlob(null);
      }
    } catch {
      setPunchError('Could not access camera. Allow camera permission and try again.');
    }
  };

  const captureSelfie = () => {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    canvas.toBlob((b) => b && setSelfieBlob(b), 'image/jpeg', 0.85);
    (video.srcObject as MediaStream)?.getTracks().forEach((t) => t.stop());
    setCameraOn(false);
  };

  const retakeSelfie = () => {
    setSelfieBlob(null);
    startCamera();
  };

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex flex-col gap-1 mb-2 text-center">
        <h1 className="text-3xl font-extrabold text-foreground">Web Attendance</h1>
        <p className="text-default-500 text-lg">GPS-verified punch with optional selfie</p>
      </div>

      <Card className="shadow-2xl border border-divider bg-content1 max-w-2xl mx-auto w-full">
        <CardBody className="p-12 flex flex-col items-center text-center">
          <div className="text-6xl font-black tabular-nums mb-2">
            {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </div>
          <p className="text-default-500 mb-6">
            {time.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>

          {location ? (
            <Chip color="success" variant="flat" startContent={<MapPin size={14} />} className="mb-4">
              GPS: {location.lat.toFixed(5)}, {location.lng.toFixed(5)}
            </Chip>
          ) : (
            <Chip color="warning" variant="flat" className="mb-4">
              {locError || 'Locating… punch is disabled until GPS is ready.'}
            </Chip>
          )}

          {cameraOn ? (
            <div className="mb-6">
              <video ref={videoRef} autoPlay playsInline muted className="rounded-xl w-64 h-48 object-cover" />
              <Button className="mt-2" color="primary" onPress={captureSelfie} startContent={<Camera size={18} />}>
                Capture Selfie
              </Button>
            </div>
          ) : selfiePreviewUrl ? (
            <div className="mb-6 flex flex-col items-center gap-2">
              <img src={selfiePreviewUrl} alt="Selfie preview" className="rounded-xl w-64 h-48 object-cover" />
              <Button variant="flat" size="sm" onPress={retakeSelfie}>
                Retake
              </Button>
            </div>
          ) : (
            <Button variant="flat" className="mb-6" onPress={startCamera} startContent={<Camera size={18} />}>
              Take Selfie (if required)
            </Button>
          )}

          {punchError && <p className="text-danger text-sm mb-4 max-w-md">{punchError}</p>}

          <Button
            className={`w-64 h-20 text-xl font-bold ${isCheckedIn ? 'bg-danger' : 'bg-primary'} text-white`}
            radius="full"
            isLoading={punchMutation.isPending}
            isDisabled={!location}
            onPress={() => punchMutation.mutate(isCheckedIn ? 'out' : 'in')}
            startContent={isCheckedIn ? <LogOut size={28} /> : <LogIn size={28} />}
          >
            {isCheckedIn ? 'PUNCH OUT' : 'PUNCH IN'}
          </Button>
          {!location && (
            <p className="text-warning text-xs mt-2">Enable location services to punch in or out.</p>
          )}
          {trackingActive && (
            <Chip color="secondary" variant="flat" className="mt-4">
              Location sharing active every {trackingIntervalMinutes} minutes
            </Chip>
          )}
        </CardBody>
      </Card>

      <div className="w-full">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Clock size={20} /> Recent Logs
        </h3>
        <Card className="border border-divider">
          <CardBody className="p-0 divide-y divide-divider">
            {isLoading ? (
              <Spinner className="m-8" />
            ) : !logsData?.length ? (
              <p className="p-8 text-center text-default-400">No punches yet</p>
            ) : (
              logsData.map((log) => (
                <div key={String(log.id)} className="p-4 flex justify-between flex-wrap gap-2">
                  <span>{String(log.date)}</span>
                  <span>In: {log.check_in ? new Date(String(log.check_in)).toLocaleTimeString() : '—'}</span>
                  <span>Out: {log.check_out ? new Date(String(log.check_out)).toLocaleTimeString() : '—'}</span>
                </div>
              ))
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
