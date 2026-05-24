'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardBody, Button, Chip, Spinner } from '@nextui-org/react';
import { MapPin, Clock, LogIn, LogOut, Camera } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { attendanceApi, unwrapList } from '@/lib/hrmsApi';

type AttendanceLog = {
  id: string;
  date?: string;
  check_in?: string | null;
  check_out?: string | null;
};

export default function WebCheckInPage() {
    const [time, setTime] = useState(new Date());
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [locError, setLocError] = useState('');
  const [selfieBlob, setSelfieBlob] = useState<Blob | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraOn, setCameraOn] = useState(false);
  const [trackingActive, setTrackingActive] = useState(false);
  const [trackingIntervalMinutes, setTrackingIntervalMinutes] = useState(10);
  const queryClient = useQueryClient();

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocError('Geolocation not supported');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setLocError('Unable to get location — enable GPS permissions'),
      { enableHighAccuracy: true }
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
      const fd = new FormData();
      if (location) {
        fd.append('lat', String(location.lat));
        fd.append('lng', String(location.lng));
      }
      if (selfieBlob) fd.append('selfie', selfieBlob, 'selfie.jpg');
      if (type === 'in') return attendanceApi.logs.punchIn(fd);
      return attendanceApi.logs.punchOut(fd);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-attendance-logs'] });
      setSelfieBlob(null);
      setCameraOn(false);
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
        { enableHighAccuracy: true }
      );
    }, Math.max(5, trackingIntervalMinutes) * 60 * 1000);
    return () => clearInterval(id);
  }, [trackingActive, trackingIntervalMinutes, isCheckedIn]);

  const startCamera = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      setCameraOn(true);
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

  return (
    <div className="w-full flex flex-col gap-6 max-w-4xl mx-auto">
      <div className="flex flex-col gap-1 mb-2 text-center">
        <h1 className="text-3xl font-extrabold text-foreground">Web Attendance</h1>
        <p className="text-default-500 text-lg">GPS-verified punch with optional selfie</p>
      </div>

      <Card className="shadow-2xl border border-divider bg-content1">
        <CardBody className="p-12 flex flex-col items-center text-center">
          <div className="text-6xl font-black tabular-nums mb-2">
            {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </div>
          <p className="text-default-500 mb-6">{time.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p>

          {location ? (
            <Chip color="success" variant="flat" startContent={<MapPin size={14} />} className="mb-4">
              GPS: {location.lat.toFixed(5)}, {location.lng.toFixed(5)}
            </Chip>
          ) : (
            <Chip color="warning" variant="flat" className="mb-4">{locError || 'Locating...'}</Chip>
          )}

          {cameraOn ? (
            <div className="mb-6">
              <video ref={videoRef} autoPlay playsInline className="rounded-xl w-64 h-48 object-cover" />
              <Button className="mt-2" color="primary" onPress={captureSelfie} startContent={<Camera size={18} />}>
                Capture Selfie
              </Button>
            </div>
          ) : (
            <Button variant="flat" className="mb-6" onPress={startCamera} startContent={<Camera size={18} />}>
              {selfieBlob ? 'Selfie captured ✓' : 'Take Selfie (if required)'}
            </Button>
          )}

          <Button
            className={`w-64 h-20 text-xl font-bold ${isCheckedIn ? 'bg-danger' : 'bg-primary'} text-white`}
            radius="full"
            isLoading={punchMutation.isPending}
            onPress={() =>
              punchMutation.mutate(isCheckedIn ? 'out' : 'in', {
                onSuccess: (resp: any) => {
                  const payload = resp?.data ?? {};
                  if (isCheckedIn) {
                    setTrackingActive(false);
                  } else if (payload.tracking_active) {
                    setTrackingActive(true);
                    setTrackingIntervalMinutes(payload.interval_minutes || 10);
                  }
                },
              })
            }
            startContent={isCheckedIn ? <LogOut size={28} /> : <LogIn size={28} />}
          >
            {isCheckedIn ? 'PUNCH OUT' : 'PUNCH IN'}
          </Button>
          {trackingActive && (
            <Chip color="secondary" variant="flat" className="mt-4">
              Location sharing active every {trackingIntervalMinutes} minutes
            </Chip>
          )}
        </CardBody>
      </Card>

      <div>
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><Clock size={20} /> Recent Logs</h3>
        <Card className="border border-divider">
          <CardBody className="p-0 divide-y divide-divider">
            {isLoading ? <Spinner className="m-8" /> : !logsData?.length ? (
              <p className="p-8 text-center text-default-400">No punches yet</p>
            ) : logsData.map((log) => (
              <div key={String(log.id)} className="p-4 flex justify-between">
                <span>{String(log.date)}</span>
                <span>In: {log.check_in ? new Date(String(log.check_in)).toLocaleTimeString() : '—'}</span>
                <span>Out: {log.check_out ? new Date(String(log.check_out)).toLocaleTimeString() : '—'}</span>
              </div>
            ))}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
