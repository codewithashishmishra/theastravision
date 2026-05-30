'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Button, Card, CardBody, Spinner, Chip } from '@nextui-org/react';
import publicApi from '@/lib/publicApi';
import { InterviewShell } from '@/components/interview/InterviewShell';

type PortalInfo = {
  job_title: string;
  email_masked: string;
  first_name: string;
  resume_uploaded: boolean;
  ai_match_score: number;
  match_threshold: number;
  outreach_status: string;
  interview_link: string | null;
};

type MatchBreakdown = {
  strengths?: string[];
  weaknesses?: string[];
  skills_met?: string[];
  skills_missed?: string[];
  recommendation?: string;
};

type MatchResult = {
  ai_match_score: number;
  match_passed: boolean;
  threshold: number;
  match_breakdown?: MatchBreakdown;
};

export default function CampaignPortalPage() {
  const { token } = useParams<{ token: string }>();
  const [info, setInfo] = useState<PortalInfo | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [resume, setResume] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [matchResult, setMatchResult] = useState<MatchResult | null>(null);

  useEffect(() => {
    publicApi
      .get(`/recruitment/portal/verify/${token}/`)
      .then((res) => setInfo(res.data))
      .catch((err) => {
        const status = err.response?.status;
        const msg = err.response?.data?.error;
        if (status === 404) setError('This link is invalid. Check the URL from your email.');
        else if (status === 403) setError(msg || 'This link is no longer available.');
        else setError(msg || 'Unable to load your invitation.');
      })
      .finally(() => setLoading(false));
  }, [token]);

  const pollParseStatus = async () => {
    for (let i = 0; i < 60; i++) {
      const res = await publicApi.get(`/recruitment/portal/${token}/parse-status/`);
      const st = res.data.resume_parse_status;
      if (st === 'ready') {
        setMatchResult({
          ai_match_score: res.data.ai_match_score,
          match_passed: res.data.match_passed,
          threshold: res.data.threshold,
          match_breakdown: res.data.match_breakdown,
        });
        setInfo((prev) =>
          prev ? { ...prev, resume_uploaded: true, ai_match_score: res.data.ai_match_score } : prev,
        );
        setParsing(false);
        return;
      }
      if (st === 'failed') {
        setError(res.data.resume_parse_error || 'Resume processing failed.');
        setParsing(false);
        return;
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
    setError('Resume processing is taking longer than expected. Please refresh in a moment.');
    setParsing(false);
  };

  const handleUpload = async () => {
    if (!resume) return;
    setUploading(true);
    setParsing(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('resume', resume);
      await publicApi.post(`/recruitment/portal/${token}/resume/`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await pollParseStatus();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string; detail?: string } } };
      setError(e.response?.data?.error || e.response?.data?.detail || 'Upload failed.');
      setParsing(false);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" color="primary" />
      </div>
    );
  }

  if (error && !info) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <Card className="max-w-md">
          <CardBody className="gap-4 p-8 text-center">
            <h1 className="text-xl font-bold text-danger">Unable to continue</h1>
            <p className="text-default-500">{error}</p>
          </CardBody>
        </Card>
      </div>
    );
  }

  if (!info) return null;

  return (
    <InterviewShell step={0} subtitle={info.job_title}>
      <p className="mb-4 text-center text-slate-400">
        Hello {info.first_name}, upload your resume to continue.
      </p>
      <Card className="border border-white/10 bg-slate-800/80">
        <CardBody className="gap-4 p-6">
          {info.interview_link ? (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-success">Your AI interview has been scheduled.</p>
              <Button as={Link} href={info.interview_link} color="primary">
                Join AI interview
              </Button>
            </div>
          ) : (
            <>
              {info.resume_uploaded && !matchResult && (
                <Chip color="success" variant="flat">
                  Resume on file — match score: {info.ai_match_score}%
                </Chip>
              )}
              {matchResult && (
                <div className="rounded-xl border border-divider p-4 text-left">
                  <p className="text-center text-2xl font-bold">{matchResult.ai_match_score}%</p>
                  <p className="text-center text-sm text-default-500">match with role requirements</p>
                  {matchResult.match_breakdown?.skills_met?.length ? (
                    <div className="mt-3">
                      <p className="text-xs font-semibold uppercase text-success">Strengths</p>
                      <ul className="mt-1 list-inside list-disc text-sm text-default-600">
                        {matchResult.match_breakdown.skills_met.slice(0, 5).map((s) => (
                          <li key={s}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {matchResult.match_breakdown?.skills_missed?.length ? (
                    <div className="mt-3">
                      <p className="text-xs font-semibold uppercase text-warning">Gaps</p>
                      <ul className="mt-1 list-inside list-disc text-sm text-default-600">
                        {matchResult.match_breakdown.skills_missed.slice(0, 5).map((s) => (
                          <li key={s}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {matchResult.match_passed ? (
                    <p className="mt-4 text-center text-success text-sm">
                      Thank you. Our team will contact you to schedule your AI interview.
                    </p>
                  ) : (
                    <p className="mt-4 text-center text-warning text-sm">
                      Thank you for applying. We will review your profile and be in touch if there is a fit.
                    </p>
                  )}
                </div>
              )}
              {!matchResult && (
                <>
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={(e) => setResume(e.target.files?.[0] ?? null)}
                  />
                  {error && <p className="text-danger text-sm">{error}</p>}
                  <Button
                    color="primary"
                    isDisabled={!resume}
                    isLoading={uploading || parsing}
                    onPress={handleUpload}
                  >
                    {parsing ? 'Analyzing resume…' : 'Upload resume & run match'}
                  </Button>
                </>
              )}
            </>
          )}
        </CardBody>
      </Card>
    </InterviewShell>
  );
}
