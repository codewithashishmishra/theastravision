'use client';

import { sanitizeHtml } from '@/lib/sanitizeHtml';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Card, CardBody, Chip, Spinner, Button } from '@nextui-org/react';
import { recruitmentApi } from '@/lib/hrmsApi';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function AiInterviewReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (id) recruitmentApi.aiReports.get(id).then((res) => setReport(res.data));
  }, [id]);

  if (!report) {
    return (
      <div className="flex justify-center p-12">
        <Spinner />
      </div>
    );
  }

  const questions = (report.questions as Array<Record<string, unknown>>) || [];
  const snapshots = (report.proctor_snapshots as Array<{ image_url?: string; image_path: string; captured_at: string }>) || [];
  const sessionVideo = report.session_recording_url as string | undefined;
  const cameraVideo = report.camera_recording_url as string | undefined;

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold">{String(report.candidate_name)}</h1>
          <p className="text-default-500">{String(report.job_title)}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Chip>Match {String(report.match_score)}%</Chip>
            {report.voice_score != null && (
              <Chip color="primary">Voice {Math.round(Number(report.voice_score))}%</Chip>
            )}
            {report.assessment_score != null && (
              <Chip color="secondary">Exam {Math.round(Number(report.assessment_score))}%</Chip>
            )}
          </div>
        </div>
        <Button as={Link} href="/recruitment/interviews" variant="flat" size="sm">
          Back to interviews
        </Button>
      </div>

      {(sessionVideo || cameraVideo) && (
        <Card>
          <CardBody className="gap-4">
            <h2 className="text-xl font-bold">Session recording</h2>
            {sessionVideo && (
              <video
                controls
                className="w-full rounded-lg border border-divider bg-black"
                src={sessionVideo}
              >
                <track kind="captions" />
              </video>
            )}
            {cameraVideo && (
              <div>
                <p className="mb-2 text-sm text-default-500">Camera feed</p>
                <video controls className="max-h-64 rounded-lg border border-divider" src={cameraVideo} />
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {report.candidate_feedback &&
      typeof report.candidate_feedback === 'object' &&
      (report.candidate_feedback as { rating?: number }).rating != null ? (
        <Card>
          <CardBody>
            <h2 className="text-xl font-bold">Candidate feedback</h2>
            <p className="text-sm">
              Rating: {(report.candidate_feedback as { rating: number }).rating} / 5
            </p>
            {(report.candidate_feedback as { comment?: string }).comment ? (
              <p className="mt-2 text-default-500">
                {(report.candidate_feedback as { comment: string }).comment}
              </p>
            ) : null}
          </CardBody>
        </Card>
      ) : null}

      {report.proctor_flags && typeof report.proctor_flags === 'object' ? (
        <Card>
          <CardBody className="gap-2 text-sm">
            <h2 className="text-xl font-bold">Proctoring</h2>
            <p>
              Tab switches:{' '}
              {String((report.proctor_flags as { tab_switch_count?: number }).tab_switch_count ?? 0)}
            </p>
            {(report.proctor_flags as { preflight_completed_at?: string }).preflight_completed_at ? (
              <p className="text-default-500">
                Pre-flight completed:{' '}
                {(report.proctor_flags as { preflight_completed_at: string }).preflight_completed_at}
              </p>
            ) : null}
          </CardBody>
        </Card>
      ) : null}

      {report.summary_html ? (
        <Card>
          <CardBody
            className="prose prose-sm max-w-none dark:prose-invert"
            dangerouslySetInnerHTML={{ html: sanitizeHtml(String(report.summary_html)) }}
          />
        </Card>
      ) : null}

      <Card>
        <CardBody className="gap-4">
          <h2 className="text-xl font-bold">Voice Q&amp;A (English transcripts)</h2>
          {questions.map((q) => (
            <div key={String(q.id)} className="border-b border-divider pb-4">
              <p className="font-medium text-primary">
                Q{q.order}: {String(q.question_text)}
                {q.skipped ? (
                  <Chip size="sm" className="ml-2" color="warning">
                    Skipped
                  </Chip>
                ) : null}
              </p>
              <p className="mt-2 text-sm">
                <span className="text-default-500">Candidate: </span>
                {String(q.candidate_transcript || '—')}
              </p>
              {q.audio_url ? (
                <audio controls className="mt-2 w-full" src={String(q.audio_url)}>
                  <track kind="captions" />
                </audio>
              ) : q.audio_path ? (
                <audio controls className="mt-2 w-full" src={`${API_BASE}/media/${q.audio_path}`} />
              ) : null}
              <p className="mt-1 text-xs text-default-400">
                Score (HR only): {q.score_percent != null ? `${Math.round(Number(q.score_percent))}%` : '—'}
              </p>
            </div>
          ))}
        </CardBody>
      </Card>

      {snapshots.length > 0 && (
        <Card>
          <CardBody className="gap-4">
            <h2 className="text-xl font-bold">Proctor snapshots</h2>
            <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
              {snapshots.map((s, i) => (
                <img
                  key={i}
                  src={s.image_url || `${API_BASE}/media/${s.image_path}`}
                  alt={`Proctor ${i + 1}`}
                  className="rounded border border-divider"
                />
              ))}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
