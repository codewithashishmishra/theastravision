'use client';

import { useState } from 'react';
import {
  Button, Chip, Input, Modal, ModalBody, ModalContent, ModalFooter, ModalHeader,
  Select, SelectItem, Table, TableBody, TableCell, TableColumn, TableHeader, TableRow,
  Textarea, useDisclosure,
} from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus } from 'lucide-react';
import { recruitmentApi, unwrapList } from '@/lib/hrmsApi';

export type Job = {
  id: string;
  title: string;
  location: string;
  status: string;
  description: string;
  employment_type: string;
  work_mode: string;
  is_published: boolean;
  slug: string;
  headcount: number;
};

type Props = {
  title: string;
  description?: string;
  filter?: { status?: string; published?: string };
  showPublishActions?: boolean;
};

const emptyForm = {
  title: '',
  location: '',
  description: '',
  status: 'Draft',
  employment_type: 'Full-time',
  work_mode: 'On-site',
  headcount: 1,
};

export function JobsManager({ title, description, filter, showPublishActions }: Props) {
  const queryClient = useQueryClient();
  const { isOpen, onOpen, onOpenChange } = useDisclosure();
  const [editing, setEditing] = useState<Job | null>(null);
  const [form, setForm] = useState(emptyForm);

  const params: Record<string, string> = {};
  if (filter?.status) params.status = filter.status;
  if (filter?.published) params.published = filter.published;

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['recruitment-jobs', params],
    queryFn: async () => unwrapList<Job>((await recruitmentApi.jobs.list(params)).data),
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload = { ...form, headcount: Number(form.headcount) };
      if (editing) return recruitmentApi.jobs.update(editing.id, payload);
      return recruitmentApi.jobs.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitment-jobs'] });
      onOpenChange();
    },
  });

  const publishMutation = useMutation({
    mutationFn: ({ id, publish }: { id: string; publish: boolean }) =>
      publish ? recruitmentApi.jobs.publish(id) : recruitmentApi.jobs.unpublish(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recruitment-jobs'] }),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    onOpen();
  };

  const openEdit = (job: Job) => {
    setEditing(job);
    setForm({
      title: job.title,
      location: job.location,
      description: job.description,
      status: job.status,
      employment_type: job.employment_type || 'Full-time',
      work_mode: job.work_mode || 'On-site',
      headcount: job.headcount || 1,
    });
    onOpen();
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">{title}</h1>
          {description && <p className="text-default-500 text-sm mt-1">{description}</p>}
        </div>
        <Button color="primary" startContent={<Plus size={16} />} onPress={openCreate}>
          New requisition
        </Button>
      </div>

      <Table aria-label="Jobs">
        <TableHeader>
          <TableColumn>TITLE</TableColumn>
          <TableColumn>LOCATION</TableColumn>
          <TableColumn>STATUS</TableColumn>
          <TableColumn>PUBLISHED</TableColumn>
          <TableColumn>ACTIONS</TableColumn>
        </TableHeader>
        <TableBody isLoading={isLoading} emptyContent="No jobs found">
          {(jobs ?? []).map((job) => (
            <TableRow key={job.id}>
              <TableCell>{job.title}</TableCell>
              <TableCell>{job.location}</TableCell>
              <TableCell>
                <Chip size="sm" variant="flat">{job.status}</Chip>
              </TableCell>
              <TableCell>
                {job.is_published ? (
                  <Chip size="sm" color="success" variant="flat">Live</Chip>
                ) : (
                  <Chip size="sm" variant="flat">Draft</Chip>
                )}
              </TableCell>
              <TableCell>
                <div className="flex gap-2 flex-wrap">
                  <Button size="sm" variant="flat" onPress={() => openEdit(job)}>Edit</Button>
                  {showPublishActions && job.status === 'Open' && !job.is_published && (
                    <Button
                      size="sm"
                      color="primary"
                      variant="flat"
                      isLoading={publishMutation.isPending}
                      onPress={() => publishMutation.mutate({ id: job.id, publish: true })}
                    >
                      Publish
                    </Button>
                  )}
                  {showPublishActions && job.is_published && (
                    <Button
                      size="sm"
                      color="warning"
                      variant="flat"
                      isLoading={publishMutation.isPending}
                      onPress={() => publishMutation.mutate({ id: job.id, publish: false })}
                    >
                      Unpublish
                    </Button>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Modal isOpen={isOpen} onOpenChange={onOpenChange} size="2xl">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>{editing ? 'Edit requisition' : 'New requisition'}</ModalHeader>
              <ModalBody className="gap-3">
                <Input label="Title" value={form.title} onValueChange={(v) => setForm({ ...form, title: v })} />
                <Input label="Location" value={form.location} onValueChange={(v) => setForm({ ...form, location: v })} />
                <div className="grid grid-cols-2 gap-3">
                  <Select
                    label="Status"
                    selectedKeys={[form.status]}
                    onSelectionChange={(k) => setForm({ ...form, status: Array.from(k)[0] as string })}
                  >
                    {['Draft', 'Open', 'On Hold', 'Closed'].map((s) => (
                      <SelectItem key={s}>{s}</SelectItem>
                    ))}
                  </Select>
                  <Input
                    type="number"
                    label="Headcount"
                    value={String(form.headcount)}
                    onValueChange={(v) => setForm({ ...form, headcount: Number(v) || 1 })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Select
                    label="Employment type"
                    selectedKeys={[form.employment_type]}
                    onSelectionChange={(k) => setForm({ ...form, employment_type: Array.from(k)[0] as string })}
                  >
                    {['Full-time', 'Part-time', 'Contract', 'Intern'].map((s) => (
                      <SelectItem key={s}>{s}</SelectItem>
                    ))}
                  </Select>
                  <Select
                    label="Work mode"
                    selectedKeys={[form.work_mode]}
                    onSelectionChange={(k) => setForm({ ...form, work_mode: Array.from(k)[0] as string })}
                  >
                    {['On-site', 'Hybrid', 'Remote'].map((s) => (
                      <SelectItem key={s}>{s}</SelectItem>
                    ))}
                  </Select>
                </div>
                <Textarea
                  label="Job description"
                  minRows={6}
                  value={form.description}
                  onValueChange={(v) => setForm({ ...form, description: v })}
                />
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>Cancel</Button>
                <Button
                  color="primary"
                  isLoading={saveMutation.isPending}
                  onPress={() => saveMutation.mutate()}
                >
                  Save
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
