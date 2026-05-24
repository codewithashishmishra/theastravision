'use client';

import React, { useState } from 'react';
import { Card, CardBody, Button, Table, TableHeader, TableBody, TableColumn, TableRow, TableCell, Chip, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Input, Checkbox } from '@nextui-org/react';
import { Calendar, Mail, Video, Link as LinkIcon, Send } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function InterviewSchedulingPage() {
  const router = useRouter();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<any>(null);
  const [ccHrAdmin, setCcHrAdmin] = useState(true);
  const [magicLink, setMagicLink] = useState('');
  const [isSending, setIsSending] = useState(false);

  const mockInterviews = [
    { id: '1', name: 'Alice Cooper', role: 'Senior Frontend Engineer', status: 'Scheduled', time: 'Today, 10:00 AM', hasLink: true },
    { id: '2', name: 'Bob Smith', role: 'Backend Developer', status: 'Pending Scheduling', time: '-', hasLink: false },
    { id: '3', name: 'Charlie Davis', role: 'Product Manager', status: 'Completed', time: 'Yesterday', hasLink: false },
  ];

  const handleOpenSchedule = (candidate: any) => {
    setSelectedCandidate(candidate);
    setMagicLink('');
    setIsModalOpen(true);
  };

  const handleSendInvite = () => {
    setIsSending(true);
    // Simulate Backend API Call
    setTimeout(() => {
      setMagicLink(`http://localhost:3000/interview/join/magic-token-abc-123`);
      setIsSending(false);
    }, 1500);
  };

  return (
    <div className="w-full flex flex-col gap-6">
      <div className="flex justify-between items-end mb-2">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-extrabold text-foreground">AI Interviews & Scheduling</h1>
          <p className="text-default-500 text-lg">Generate Magic Links and monitor live AI-driven interviews.</p>
        </div>
      </div>

      <Card className="shadow-sm border border-divider">
        <CardBody className="p-0">
          <Table removeWrapper aria-label="Interviews Table">
            <TableHeader>
              <TableColumn>CANDIDATE</TableColumn>
              <TableColumn>ROLE</TableColumn>
              <TableColumn>STATUS</TableColumn>
              <TableColumn>SCHEDULED TIME</TableColumn>
              <TableColumn align="center">ACTIONS</TableColumn>
            </TableHeader>
            <TableBody>
              {mockInterviews.map((item) => (
                <TableRow key={item.id} className="border-b border-divider hover:bg-default-50 transition-colors">
                  <TableCell className="py-4 font-bold">{item.name}</TableCell>
                  <TableCell>{item.role}</TableCell>
                  <TableCell>
                    <Chip size="sm" color={item.status === 'Scheduled' ? 'primary' : item.status === 'Completed' ? 'success' : 'warning'} variant="flat">
                      {item.status}
                    </Chip>
                  </TableCell>
                  <TableCell className="text-default-500 font-medium">{item.time}</TableCell>
                  <TableCell>
                    <div className="flex justify-center gap-2">
                      {item.status === 'Scheduled' ? (
                         <Button size="sm" color="danger" variant="flat" className="font-bold animate-pulse" startContent={<Video size={14} />} onPress={() => router.push(`/recruitment/interviews/${item.id}/live`)}>
                           Watch Live
                         </Button>
                      ) : item.status === 'Pending Scheduling' ? (
                         <Button size="sm" color="primary" variant="flat" className="font-bold" startContent={<Calendar size={14} />} onPress={() => handleOpenSchedule(item)}>
                           Schedule & Invite
                         </Button>
                      ) : (
                         <Button size="sm" variant="flat" className="font-bold text-default-500">View Report</Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardBody>
      </Card>

      <Modal isOpen={isModalOpen} onOpenChange={setIsModalOpen} size="md">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1">Schedule AI Interview</ModalHeader>
              <ModalBody>
                <div className="flex flex-col gap-4">
                  <p className="text-sm text-default-500">
                    You are generating a secure Magic Link for <b>{selectedCandidate?.name}</b>. The candidate does not need an account to join.
                  </p>
                  
                  <Input type="datetime-local" label="Scheduled Time" variant="bordered" isRequired />
                  <Input type="number" label="Link Expiry (Minutes)" variant="bordered" defaultValue="30" min={15} max={120} description="How long the link is valid once the interview starts." />
                  
                  <div className="p-4 bg-default-50 rounded-xl border border-divider flex flex-col gap-2">
                    <h4 className="text-sm font-bold flex items-center gap-2"><Mail size={16}/> Email Notifications</h4>
                    <Checkbox isSelected color="primary" isReadOnly>Send Direct Email to Candidate</Checkbox>
                    <Checkbox isSelected={ccHrAdmin} onValueChange={setCcHrAdmin} color="secondary">CC HR Admin (hradmin@aastraa.com)</Checkbox>
                  </div>

                  {magicLink && (
                    <div className="p-3 bg-success/10 border border-success/30 rounded-xl mt-2">
                      <p className="text-xs font-bold text-success mb-1 flex items-center gap-1"><LinkIcon size={12}/> Magic Link Generated</p>
                      <p className="text-xs break-all text-success-700 select-all">{magicLink}</p>
                    </div>
                  )}
                </div>
              </ModalBody>
              <ModalFooter>
                <Button color="danger" variant="light" onPress={onClose}>Close</Button>
                {!magicLink ? (
                  <Button color="primary" className="font-bold shadow-lg shadow-primary/30" onPress={handleSendInvite} isLoading={isSending} startContent={!isSending && <Send size={16}/>}>
                    Generate & Send Invite
                  </Button>
                ) : (
                  <Button color="success" className="font-bold shadow-lg shadow-success/30" onPress={onClose}>
                    Done
                  </Button>
                )}
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>
    </div>
  );
}
