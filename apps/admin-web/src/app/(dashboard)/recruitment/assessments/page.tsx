'use client';

import { useEffect, useState } from 'react';
import { Button, Card, CardBody, Select, SelectItem, Spinner } from '@nextui-org/react';
import { recruitmentApi } from '@/lib/hrmsApi';

type Template = {
  id: string;
  job: string;
  duration_minutes: number;
  question_count: number;
  questions?: Array<{ order: number; prompt: string }>;
};

type Job = { id: string; title: string; assessment_enabled?: boolean };

export default function AssessmentsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [jobId, setJobId] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const load = () => {
    recruitmentApi.jobs.list().then((res) => {
      const list = res.data.results ?? res.data;
      setJobs(Array.isArray(list) ? list : []);
    });
    recruitmentApi.assessmentTemplates.list().then((res) => {
      const list = res.data.results ?? res.data;
      setTemplates(Array.isArray(list) ? list : []);
    });
  };

  useEffect(() => {
    load();
  }, []);

  const handleEnableAssessment = async () => {
    if (!jobId) return;
    await recruitmentApi.jobs.update(jobId, { assessment_enabled: true });
    const existing = templates.find((t) => t.job === jobId);
    if (!existing) {
      await recruitmentApi.assessmentTemplates.create({
        job: jobId,
        duration_minutes: 20,
        question_count: 10,
      });
    }
    setMessage('Assessment enabled for this job.');
    load();
  };

  const handleGenerate = async (templateId: string) => {
    setLoading(true);
    try {
      await recruitmentApi.assessmentTemplates.generate(templateId);
      setMessage('Generated 10 MCQ questions from AI.');
      load();
    } catch {
      setMessage('Generation failed. Check OpenAI config.');
    } finally {
      setLoading(false);
    }
  };

  const jobTemplates = templates.filter((t) => t.job === jobId);

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div>
        <h1 className="text-3xl font-extrabold">Assessment builder</h1>
        <p className="text-default-500">20-minute, 10-question proctored MCQ exams after voice interview.</p>
      </div>
      <Card>
        <CardBody className="gap-4">
          <Select label="Job" selectedKeys={jobId ? [jobId] : []} onSelectionChange={(k) => setJobId(String(Array.from(k)[0] || ''))}>
            {jobs.map((j) => (
              <SelectItem key={j.id}>
                {j.title} {j.assessment_enabled ? '(enabled)' : ''}
              </SelectItem>
            ))}
          </Select>
          <Button onPress={handleEnableAssessment} isDisabled={!jobId}>
            Enable assessment for job
          </Button>
        </CardBody>
      </Card>
      {jobTemplates.map((t) => (
        <Card key={t.id}>
          <CardBody className="gap-3">
            <p>
              {t.question_count} questions · {t.duration_minutes} min
            </p>
            <Button color="primary" isLoading={loading} onPress={() => handleGenerate(t.id)}>
              Generate questions with AI
            </Button>
            <ul className="text-sm text-default-500">
              {(t.questions || []).slice(0, 3).map((q) => (
                <li key={q.order}>
                  {q.order}. {q.prompt.slice(0, 80)}…
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      ))}
      {message && <p className="text-sm">{message}</p>}
      {loading && <Spinner />}
    </div>
  );
}
