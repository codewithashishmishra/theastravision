'use client';

import { useEffect, useRef, useState } from 'react';
import { Modal, ModalBody, ModalContent, ModalHeader, Spinner } from '@nextui-org/react';
import { AxiosError } from 'axios';
import { wfhApi } from '@/lib/wfhApi';
import { parseApiError } from '@/lib/parseApiError';
import { formatRegionalDateTime } from '@/lib/formatDateTime';
import { acquireScreenshotSlot, releaseScreenshotSlot } from '@/lib/screenshotLoadQueue';

type Props = {
  screenshotId: string;
  monitor: number;
  capturedAt: string;
};

function isJpegBlob(blob: Blob): boolean {
  return blob.type.includes('image') || blob.type === 'application/octet-stream';
}

async function blobToImageUrl(blob: Blob): Promise<string> {
  if (!isJpegBlob(blob)) {
    const text = await blob.text();
    try {
      const err = JSON.parse(text);
      throw new Error(
        typeof err.detail === 'string' ? err.detail : 'Screenshot could not be decrypted'
      );
    } catch (e) {
      if (e instanceof Error && e.message !== 'Screenshot could not be decrypted') {
        throw e;
      }
      throw new Error(text.slice(0, 120) || 'Screenshot could not be decrypted');
    }
  }
  return URL.createObjectURL(blob);
}

export default function ScreenshotThumb({ screenshotId, monitor, capturedAt }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [lightbox, setLightbox] = useState(false);

  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => setInView(entry.isIntersecting),
      { rootMargin: '120px' }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!inView) return;

    let objectUrl: string | null = null;
    let cancelled = false;

    setLoading(true);
    setError(null);

    const load = async () => {
      await acquireScreenshotSlot();
      if (cancelled) {
        releaseScreenshotSlot();
        return;
      }
      try {
        const res = await wfhApi.screenshotImage(screenshotId);
        if (cancelled) return;
        objectUrl = await blobToImageUrl(res.data);
        setUrl(objectUrl);
      } catch (e: unknown) {
        if (cancelled) return;
        let msg = parseApiError(e, 'Could not load screenshot');
        if (e instanceof AxiosError && e.response?.status === 422) {
          msg = 'Session encryption key missing — re-capture from an updated tracker.';
        }
        setError(msg);
      } finally {
        releaseScreenshotSlot();
        if (!cancelled) setLoading(false);
      }
    };

    void load();

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [inView, screenshotId]);

  const timeLabel = new Date(capturedAt).toLocaleTimeString();

  return (
    <>
      <div ref={rootRef} className="flex flex-col gap-1">
        <button
          type="button"
          className="aspect-video rounded-lg overflow-hidden bg-default-100 border border-divider relative w-full cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary"
          onClick={() => url && setLightbox(true)}
          disabled={!url}
        >
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Spinner size="sm" />
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center p-2 text-center text-xs text-danger">
              {error}
            </div>
          )}
          {url && (
            <img
              src={url}
              alt={`Monitor ${monitor} at ${timeLabel}`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          )}
          {!loading && !error && !url && (
            <div className="absolute inset-0 flex items-center justify-center text-xs text-default-500">
              {inView ? 'Loading…' : 'Scroll to load'}
            </div>
          )}
        </button>
        <p className="text-xs text-default-500 text-center">
          Monitor {monitor} · {timeLabel}
        </p>
        <p className="text-xs text-default-400 truncate text-center">ID: {screenshotId.slice(0, 8)}…</p>
      </div>

      <Modal isOpen={lightbox} onClose={() => setLightbox(false)} size="5xl">
        <ModalContent>
          <ModalHeader>
            Monitor {monitor} — {formatRegionalDateTime(capturedAt)}
          </ModalHeader>
          <ModalBody className="pb-6">
            {url && (
              <img
                src={url}
                alt={`Screenshot monitor ${monitor}`}
                className="w-full max-h-[80vh] object-contain rounded-lg"
              />
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
}
