'use client';

import { useEffect, useState } from 'react';
import {
  Button,
  Card,
  CardBody,
  Checkbox,
  Input,
  Select,
  SelectItem,
  Spinner,
} from '@nextui-org/react';
import { recruitmentApi } from '@/lib/hrmsApi';

type Job = { id: string; title: string; match_threshold?: number; assessment_enabled?: boolean; auto_send_invite?: boolean };

export default function NewCandidateInterviewPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobId, setJobId] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [resume, setResume] = useState<File | null>(null);
  const [candidateId, setCandidateId] = useState<string | null>(null);
  const [matchScore, setMatchScore] = useState<number | null>(null);
  const [matchPassed, setMatchPassed] = useState(false);
  const [magicLink, setMagicLink] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [sendEmail, setSendEmail] = useState(false);

  useEffect(() => {
    recruitmentApi.jobs.list().then((res) => {
      const list = res.data.results ?? res.data;
      setJobs(Array.isArray(list) ? list : []);
    });
  }, []);

  const selectedJob = jobs.find((j) => j.id === jobId);

  const handleCreate = async () => {
    if (!jobId || !resume) {
      setMessage('Select a job and upload a resume.');
      return;
    }
    const ext = resume.name.toLowerCase();
    if (!ext.endsWith('.pdf') && !ext.endsWith('.docx')) {
      setMessage('Resume must be a PDF or DOCX file.');
      return;
    }
    setLoading(true);
    setMessage('');
    const form = new FormData();
    form.append('job', jobId);
    form.append('first_name', firstName);
    form.append('last_name', lastName);
    form.append('email', email);
    form.append('resume_file', resume);
    try {
      const res = await recruitmentApi.candidates.create(form);
      setCandidateId(res.data.id);
      setMessage('Candidate created. Running AI match…');
      const matchRes = await recruitmentApi.candidates.match(res.data.id);
      setMatchScore(matchRes.data.new_score);
      setMatchPassed(matchRes.data.match_passed);
      setSendEmail(selectedJob?.auto_send_invite ?? false);
    } catch {
      setMessage('Failed to create or match candidate.');
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async () => {
    if (!candidateId) return;
    setLoading(true);
    try {
      const res = await recruitmentApi.candidates.invite(candidateId, { send_email: sendEmail });
      setMagicLink(res.data.magic_link);
      setMessage('Interview link ready.');
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } };
      setMessage(e.response?.data?.error || 'Invite failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6 p-2">
      <div>
        <h1 className="text-3xl font-extrabold">AI interview — add candidate</h1>
        <p className="text-default-500">Upload JD-linked resume, match at 70%+, then share the Astra interview link.</p>
      </div>
      <Card>
        <CardBody className="gap-4">
          <Select label="Job requisition" selectedKeys={jobId ? [jobId] : []} onSelectionChange={(k) => setJobId(String(Array.from(k)[0] || ''))}>
            {jobs.map((j) => (
              <SelectItem key={j.id}>{j.title}</SelectItem>
            ))}
          </Select>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input label="First name" value={firstName} onValueChange={setFirstName} />
            <Input label="Last name" value={lastName} onValueChange={setLastName} />
          </div>
          <Input label="Email" type="email" value={email} onValueChange={setEmail} />
          <Input type="file" label="Resume (PDF/DOCX)" accept=".pdf,.docx" onChange={(e) => setResume(e.target.files?.[0] ?? null)} />
          <Button color="primary" isLoading={loading} onPress={handleCreate}>
            Upload & run AI match
          </Button>
        </CardBody>
      </Card>
      {matchScore !== null && (
        <Card className={matchPassed ? 'border-success' : 'border-warning'}>
          <CardBody className="gap-3">
            <p className="text-lg font-bold">
              Match score: {matchScore}% (threshold {selectedJob?.match_threshold ?? 70}%)
            </p>
            <p className={matchPassed ? 'text-success' : 'text-warning'}>
              {matchPassed ? 'Qualified for AI interview.' : 'Below threshold — adjust JD or resume.'}
            </p>
            {matchPassed && (
              <>
                <Checkbox isSelected={sendEmail} onValueChange={setSendEmail}>
                  Email interview link to candidate
                </Checkbox>
                <Button color="secondary" isLoading={loading} onPress={handleInvite}>
                  Generate interview link
                </Button>
              </>
            )}
          </CardBody>
        </Card>
      )}
      {magicLink && (
        <Card>
          <CardBody className="gap-2">
            <p className="font-semibold">Share with candidate</p>
            <Input readOnly value={magicLink} />
            <Button variant="flat" onPress={() => navigator.clipboard.writeText(magicLink)}>
              Copy link
            </Button>
          </CardBody>
        </Card>
      )}
      {message && <p className="text-sm text-default-500">{message}</p>}
      {loading && <Spinner />}
    </div>
  );
}
