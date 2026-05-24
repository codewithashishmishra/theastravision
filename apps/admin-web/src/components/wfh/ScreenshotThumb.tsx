'use client';

import { useEffect, useState } from 'react';
import { Modal, ModalBody, ModalContent, ModalHeader, Spinner } from '@nextui-org/react';
import { AxiosError } from 'axios';
import { wfhApi } from '@/lib/wfhApi';
import { parseApiError } from '@/lib/parseApiError';

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
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [lightbox, setLightbox] = useState(false);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;

    setLoading(true);
    setError(null);
    setUrl(null);

    wfhApi
      .screenshotImage(screenshotId)
      .then(async (res) => {
        if (cancelled) return;
        objectUrl = await blobToImageUrl(res.data);
        setUrl(objectUrl);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        let msg = parseApiError(e, 'Could not load screenshot');
        if (e instanceof AxiosError && e.response?.status === 422) {
          msg = 'Session encryption key missing — re-capture from an updated tracker.';
        }
        setError(msg);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [screenshotId]);

  const timeLabel = new Date(capturedAt).toLocaleTimeString();

  return (
    <>
      <div className="flex flex-col gap-1">
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
            />
          )}
          {!loading && !error && !url && (
            <div className="absolute inset-0 flex items-center justify-center text-xs text-default-500">
              No preview
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
            Monitor {monitor} — {new Date(capturedAt).toLocaleString()}
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
