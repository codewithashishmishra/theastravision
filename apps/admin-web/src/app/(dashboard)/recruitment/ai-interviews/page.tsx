'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardBody,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableColumn,
  TableHeader,
  TableRow,
} from '@nextui-org/react';
import { recruitmentApi } from '@/lib/hrmsApi';

type ReportRow = {
  id: string;
  candidate_name: string;
  job_title: string;
  session_status: string;
  match_score: number;
  voice_score: number | null;
  assessment_score: number | null;
  created_at: string;
};

export default function AiInterviewsPage() {
  const router = useRouter();
  const [rows, setRows] = useState<ReportRow[]>([]);

  useEffect(() => {
    recruitmentApi.aiReports.list().then((res) => {
      const list = res.data.results ?? res.data;
      setRows(Array.isArray(list) ? list : []);
    });
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-extrabold">AI interview reports</h1>
        <p className="text-default-500">Astra voice interviews, assessments, and HR reports.</p>
      </div>
      <Card>
        <CardBody className="p-0">
          <Table removeWrapper aria-label="AI reports">
            <TableHeader>
              <TableColumn>CANDIDATE</TableColumn>
              <TableColumn>ROLE</TableColumn>
              <TableColumn>STATUS</TableColumn>
              <TableColumn>MATCH</TableColumn>
              <TableColumn>VOICE</TableColumn>
              <TableColumn>EXAM</TableColumn>
            </TableHeader>
            <TableBody emptyContent="No reports yet.">
              {rows.map((r) => (
                <TableRow
                  key={r.id}
                  className="cursor-pointer hover:bg-default-50"
                  onClick={() => router.push(`/recruitment/ai-interviews/${r.id}`)}
                >
                  <TableCell className="font-semibold">{r.candidate_name}</TableCell>
                  <TableCell>{r.job_title}</TableCell>
                  <TableCell>
                    <Chip size="sm" variant="flat">
                      {r.session_status}
                    </Chip>
                  </TableCell>
                  <TableCell>{r.match_score}%</TableCell>
                  <TableCell>{r.voice_score != null ? `${Math.round(r.voice_score)}%` : '—'}</TableCell>
                  <TableCell>{r.assessment_score != null ? `${Math.round(r.assessment_score)}%` : '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}
