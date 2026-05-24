'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Button,
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

type Candidate = {
  id: string;
  first_name: string;
  last_name: string;
  job_title: string;
  ai_match_score: number;
  match_breakdown?: { recommendation?: string };
};

export default function AiScoresPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);

  useEffect(() => {
    recruitmentApi.candidates.list().then((res) => {
      const list = res.data.results ?? res.data;
      setCandidates(Array.isArray(list) ? list : []);
    });
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-extrabold">AI match scores</h1>
          <p className="text-default-500">Resume vs JD matching before Astra interview.</p>
        </div>
        <Button as={Link} href="/recruitment/candidates/new" color="primary">
          Add candidate
        </Button>
      </div>
      <Card>
        <CardBody className="p-0">
          <Table removeWrapper>
            <TableHeader>
              <TableColumn>CANDIDATE</TableColumn>
              <TableColumn>ROLE</TableColumn>
              <TableColumn>SCORE</TableColumn>
              <TableColumn>RECOMMENDATION</TableColumn>
            </TableHeader>
            <TableBody>
              {candidates.map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-semibold">
                    {c.first_name} {c.last_name}
                  </TableCell>
                  <TableCell>{c.job_title}</TableCell>
                  <TableCell>
                    <Chip color={c.ai_match_score >= 70 ? 'success' : 'warning'} variant="flat">
                      {c.ai_match_score}%
                    </Chip>
                  </TableCell>
                  <TableCell className="text-sm text-default-500">
                    {c.match_breakdown?.recommendation || '—'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>
    </div>
  );
}
