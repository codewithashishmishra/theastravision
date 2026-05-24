'use client';

import React, { useState } from 'react';
import {
  Card, CardBody, Button, Progress, Spinner, Input, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter,
} from '@nextui-org/react';
import { ClipboardList, Upload } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '@/lib/axios';
import { employeesApi, unwrapList } from '@/lib/hrmsApi';

type Assignment = {
  id: string;
  progress: number;
  status: string;
};

export default function OnboardingChecklistsPage() {
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [docType, setDocType] = useState('Offer Letter');
  const [employeeId, setEmployeeId] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['onboarding-assignments'],
    queryFn: async () => {
      const res = await api.get('/onboarding/assignments/');
      return unwrapList<Assignment>(res.data);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file || !employeeId) throw new Error('Missing file or employee');
      const fd = new FormData();
      fd.append('employee', employeeId);
      fd.append('document_type', docType);
      fd.append('file', file);
      return employeesApi.documents.upload(fd);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['onboarding-assignments'] });
      setUploadOpen(false);
      setFile(null);
    },
  });

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider">
        <div>
          <h1 className="text-2xl font-extrabold flex items-center gap-2">
            <ClipboardList className="text-primary" /> Onboarding Tracker
          </h1>
          <p className="text-sm text-default-500 mt-1">Manage new hire tasks and document uploads</p>
        </div>
        <Button color="primary" startContent={<Upload size={18} />} onPress={() => setUploadOpen(true)}>
          Upload Document
        </Button>
      </div>

      {isLoading ? (
        <Spinner />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {(data ?? []).map((a) => (
            <Card key={a.id} className="border border-divider">
              <CardBody className="p-6">
                <p className="font-bold mb-2">Assignment {a.id.slice(0, 8)}</p>
                <Progress value={a.progress} color="primary" className="mb-2" />
                <p className="text-sm text-default-500">Status: {a.status}</p>
              </CardBody>
            </Card>
          ))}
        </div>
      )}

      <Modal isOpen={uploadOpen} onOpenChange={setUploadOpen}>
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader>Upload Onboarding Document</ModalHeader>
              <ModalBody className="gap-4">
                <Input label="Employee ID" value={employeeId} onValueChange={setEmployeeId} />
                <Input label="Document Type" value={docType} onValueChange={setDocType} />
                <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
              </ModalBody>
              <ModalFooter>
                <Button variant="light" onPress={onClose}>Cancel</Button>
                <Button color="primary" isLoading={uploadMutation.isPending} onPress={() => uploadMutation.mutate()}>
                  Upload
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
