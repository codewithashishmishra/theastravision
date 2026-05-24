import { sanitizeHtml } from '@/lib/sanitizeHtml';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardBody, Chip, Spinner } from '@nextui-org/react';
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
  const snapshots = (report.proctor_snapshots as Array<{ image_path: string; captured_at: string }>) || [];

  return (
    <div className="flex max-w-4xl flex-col gap-6">
      <div>
        <h1 className="text-3xl font-extrabold">{String(report.candidate_name)}</h1>
        <p className="text-default-500">{String(report.job_title)}</p>
        <div className="mt-2 flex gap-2">
          <Chip>Match {String(report.match_score)}%</Chip>
          {report.voice_score != null && <Chip color="primary">Voice {Math.round(Number(report.voice_score))}%</Chip>}
          {report.assessment_score != null && (
            <Chip color="secondary">Exam {Math.round(Number(report.assessment_score))}%</Chip>
          )}
        </div>
      </div>
      {report.summary_html ? (
        <Card>
          <CardBody
            className="prose prose-sm max-w-none dark:prose-invert"
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(String(report.summary_html)) }}
          />
        </Card>
      ) : null}
      <Card>
        <CardBody className="gap-4">
          <h2 className="text-xl font-bold">Voice Q&amp;A</h2>
          {questions.map((q) => (
            <div key={String(q.id)} className="border-b border-divider pb-4">
              <p className="font-medium">{String(q.question_text)}</p>
              <p className="mt-1 text-sm text-default-500">{String(q.candidate_transcript || '—')}</p>
              <p className="text-sm text-primary">Score: {q.score_percent != null ? `${Math.round(Number(q.score_percent))}%` : '—'}</p>
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
                  src={`${API_BASE}/media/${s.image_path}`}
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
