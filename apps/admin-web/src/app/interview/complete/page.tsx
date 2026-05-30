'use client';

import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Button, Card, CardBody, Textarea } from '@nextui-org/react';
import publicApi from '@/lib/publicApi';
import { AstraAvatar, InterviewShell } from '@/components/interview/InterviewShell';

function CompleteContent() {
  const params = useSearchParams();
  const sessionId = params.get('sessionId');
  const reason = params.get('reason');
  const skipLimit = reason === 'skip_limit';
  const [rating, setRating] = useState<number | null>(null);
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [saving, setSaving] = useState(false);

  const submitFeedback = async () => {
    if (!sessionId || rating === null) return;
    setSaving(true);
    try {
      await publicApi.post(`/recruitment/ai-sessions/${sessionId}/feedback/`, {
        rating,
        comment,
      });
      setSubmitted(true);
    } catch {
      setSubmitted(true);
    } finally {
      setSaving(false);
    }
  };

  return (
    <InterviewShell step={4}>
      <Card className="border border-white/10 bg-slate-800/80">
        <CardBody className="gap-6 p-8 text-center">
          <AstraAvatar />
          <h1 className="text-2xl font-bold">{skipLimit ? 'Interview ended' : 'Thank you!'}</h1>
          <p className="text-slate-400">
            {skipLimit
              ? 'Interview ended because the skip limit was reached. Thank you for your time.'
              : 'Your interview with Astra has been recorded. Our HR team will review your session and contact you soon with next steps.'}
          </p>
          {!submitted && sessionId && (
            <div className="mt-4 space-y-4 text-left">
              <p className="text-sm font-medium text-slate-300">
                How was your experience with the AI-based interview?
              </p>
              <div className="flex justify-center gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <Button
                    key={n}
                    size="sm"
                    variant={rating === n ? 'solid' : 'bordered'}
                    color={rating === n ? 'warning' : 'default'}
                    aria-label={`Rate interview ${n} out of 5`}
                    onPress={() => setRating(n)}
                  >
                    {n}
                  </Button>
                ))}
              </div>
              <Textarea
                label="Optional comments"
                placeholder="Tell us what worked well or what we could improve…"
                value={comment}
                onValueChange={setComment}
                minRows={3}
              />
              <Button
                color="primary"
                className="w-full"
                isDisabled={rating === null}
                isLoading={saving}
                onPress={submitFeedback}
              >
                Submit feedback
              </Button>
            </div>
          )}
          {submitted && (
            <p className="text-sm text-success">Thank you for your feedback.</p>
          )}
        </CardBody>
      </Card>
    </InterviewShell>
  );
}

export default function InterviewCompletePage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-950" />}>
      <CompleteContent />
    </Suspense>
  );
}
