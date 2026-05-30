'use client';

import React, { useEffect, useState } from 'react';
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Button,
  Input,
  Select,
  SelectItem,
  Checkbox,
} from '@nextui-org/react';
import { employeesApi, recruitmentApi, unwrapList } from '@/lib/hrmsApi';
import { SampleFileDownload } from '@/components/common/SampleFileDownload';

type ManagerOption = {
  id: string;
  first_name: string;
  last_name: string;
  employee_code: string;
};

type Props = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
};

export function CreateCampaignModal({ isOpen, onOpenChange, onCreated }: Props) {
  const [title, setTitle] = useState('');
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [managerId, setManagerId] = useState('');
  const [launchNow, setLaunchNow] = useState(true);
  const [managers, setManagers] = useState<ManagerOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isOpen) return;
    employeesApi.list({ page_size: '500', status: 'Active' }).then((res) => {
      setManagers(unwrapList<ManagerOption>(res.data));
    });
  }, [isOpen]);

  const reset = () => {
    setTitle('');
    setJdFile(null);
    setImportFile(null);
    setError('');
  };

  const submit = async () => {
    if (!title.trim()) {
      setError('Campaign title is required.');
      return;
    }
    if (!managerId) {
      setError('Select a default reporting manager.');
      return;
    }
    if (!importFile) {
      setError('Upload a CSV or Excel file with candidate emails.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const fd = new FormData();
      fd.append('title', title.trim());
      fd.append('default_reporting_manager', managerId);
      if (jdFile) fd.append('jd_file', jdFile);
      fd.append('file', importFile);
      if (launchNow) fd.append('launch', 'true');
      await recruitmentApi.campaigns.create(fd);
      reset();
      onOpenChange(false);
      onCreated();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string; file?: string[] } } };
      setError(
        e.response?.data?.detail ||
          (Array.isArray(e.response?.data?.file) ? e.response?.data.file[0] : null) ||
          'Failed to create campaign.',
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) reset();
        onOpenChange(open);
      }}
      size="2xl"
      scrollBehavior="inside"
    >
      <ModalContent>
        {(onClose) => (
          <>
            <ModalHeader>Create interview campaign</ModalHeader>
            <ModalBody className="gap-4">
              <Input
                label="Role title"
                placeholder="e.g. Python developer"
                value={title}
                onValueChange={setTitle}
                variant="bordered"
                isRequired
              />
              <div>
                <p className="text-sm text-default-500 mb-2">Job description (PDF or DOCX)</p>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
                />
              </div>
              <Select
                label="Default reporting manager"
                variant="bordered"
                selectedKeys={managerId ? [managerId] : []}
                onSelectionChange={(keys) => setManagerId(String(Array.from(keys)[0] ?? ''))}
                isRequired
              >
                {managers.map((m) => (
                  <SelectItem key={m.id}>
                    {m.first_name} {m.last_name} ({m.employee_code})
                  </SelectItem>
                ))}
              </Select>
              <div>
                <p className="text-sm text-default-500 mb-2">
                  Candidate list (CSV or Excel with email column)
                </p>
                <div className="flex flex-wrap gap-2 items-center">
                  <SampleFileDownload
                    href="/samples/interview-campaign-candidates.csv"
                    filename="interview-campaign-candidates.csv"
                    label="Sample CSV"
                  />
                  <SampleFileDownload
                    href="/samples/interview-campaign-candidates.xlsx"
                    filename="interview-campaign-candidates.xlsx"
                    label="Sample Excel"
                  />
                  <label>
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      className="hidden"
                      onChange={(e) => setImportFile(e.target.files?.[0] ?? null)}
                    />
                    <Button as="span" size="sm" variant="bordered" color={importFile ? 'primary' : 'default'}>
                      {importFile ? importFile.name : 'Upload CSV / Excel'}
                    </Button>
                  </label>
                </div>
              </div>
              <Checkbox isSelected={launchNow} onValueChange={setLaunchNow}>
                Send outreach emails after create (10 per minute)
              </Checkbox>
              {error && <p className="text-danger text-sm">{error}</p>}
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onClose}>
                Cancel
              </Button>
              <Button color="primary" isLoading={loading} onPress={submit}>
                Create campaign
              </Button>
            </ModalFooter>
          </>
        )}
      </ModalContent>
    </Modal>
  );
}
