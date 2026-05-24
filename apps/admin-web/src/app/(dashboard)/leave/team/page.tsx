'use client';

import React, { useState } from 'react';
import { 
  Button, Card, CardBody, Avatar, Chip, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, useDisclosure 
} from "@nextui-org/react";
import { Calendar as CalendarIcon, Check, X, AlertTriangle, Users } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from '@/lib/axios';

export default function TeamLeaveCalendarPage() {
  const queryClient = useQueryClient();
  
  // Custom Approval/Reject Modal States
  const {isOpen, onOpen, onOpenChange} = useDisclosure();
  const [selectedRequest, setSelectedRequest] = useState<any>(null);
  const [actionType, setActionType] = useState<'Approve' | 'Reject'>('Approve');

  // Fetch Leave Requests (Approvals Inbox)
  const { data: requests = [], isLoading } = useQuery({
    queryKey: ['leave_requests'],
    queryFn: async () => {
      try {
        const res = await axios.get('/leave/requests/?status=Pending');
        return res.data.results || [];
      } catch {
        return MOCK_REQUESTS; // Fallback
      }
    }
  });

  const MOCK_REQUESTS = [
    { id: '1', employee_name: 'John Doe', avatar: 'https://i.pravatar.cc/150?u=1', type: 'Sick Leave', start_date: '2026-05-24', end_date: '2026-05-25', duration: 2, status: 'Pending', reason: 'Fever and cold' },
    { id: '2', employee_name: 'Sarah Smith', avatar: 'https://i.pravatar.cc/150?u=2', type: 'Earned Leave', start_date: '2026-06-10', end_date: '2026-06-15', duration: 5, status: 'Pending', reason: 'Family vacation' },
  ];

  const actionMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string, status: string }) => {
      return axios.patch(`/leave/requests/${id}/`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leave_requests'] });
      onOpenChange();
    },
    onError: () => {
      // Fallback
      onOpenChange();
    }
  });

  const handleAction = () => {
    if (selectedRequest) {
      actionMutation.mutate({
        id: selectedRequest.id,
        status: actionType === 'Approve' ? 'Approved' : 'Rejected'
      });
    }
  };

  return (
    <div className="w-full flex flex-col gap-6">
      
      {/* Header */}
      <div className="flex justify-between items-center bg-content1 p-6 rounded-3xl border border-divider shadow-sm">
        <div>
          <h1 className="text-2xl font-extrabold text-foreground flex items-center gap-2">
            <Users className="text-primary" size={28} />
            Team Leaves & Approvals
          </h1>
          <p className="text-sm text-default-500 mt-1">
            Review your team's upcoming time off and manage pending leave requests.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: Pending Approvals */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <h2 className="text-lg font-bold text-foreground">Pending Requests</h2>
          {requests.map((req: any) => (
            <Card key={req.id} className="w-full shadow-sm border border-divider">
              <CardBody className="p-4 flex flex-row items-center justify-between">
                <div className="flex items-center gap-4">
                  <Avatar src={req.avatar} size="lg" className="border-2 border-primary/20" />
                  <div className="flex flex-col">
                    <span className="font-bold text-[16px]">{req.employee_name}</span>
                    <span className="text-xs text-default-500">{req.type} • {req.duration} Days</span>
                    <span className="text-xs font-medium text-foreground mt-1">
                      {req.start_date} to {req.end_date}
                    </span>
                    <span className="text-xs text-default-400 italic mt-0.5">"{req.reason}"</span>
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <Button 
                    size="sm" 
                    color="success" 
                    variant="flat"
                    className="font-bold w-24"
                    startContent={<Check size={14} />}
                    onPress={() => {
                      setSelectedRequest(req);
                      setActionType('Approve');
                      onOpen();
                    }}
                  >
                    Approve
                  </Button>
                  <Button 
                    size="sm" 
                    color="danger" 
                    variant="flat"
                    className="font-bold w-24"
                    startContent={<X size={14} />}
                    onPress={() => {
                      setSelectedRequest(req);
                      setActionType('Reject');
                      onOpen();
                    }}
                  >
                    Reject
                  </Button>
                </div>
              </CardBody>
            </Card>
          ))}
          {requests.length === 0 && (
            <div className="p-8 text-center text-default-400 bg-content1 rounded-2xl border border-divider">
              All caught up! No pending leave requests.
            </div>
          )}
        </div>

        {/* Right Col: Mini Team Calendar */}
        <div className="flex flex-col gap-4">
          <h2 className="text-lg font-bold text-foreground">Upcoming Absences</h2>
          <Card className="w-full shadow-sm border border-divider bg-primary/5">
            <CardBody className="p-6 text-center">
              <CalendarIcon size={48} className="text-primary/40 mx-auto mb-4" />
              <p className="font-bold text-lg mb-2">Team is fully staffed today.</p>
              <p className="text-sm text-default-500">Sarah Smith is out next week (Jun 10 - Jun 15).</p>
            </CardBody>
          </Card>
        </div>

      </div>

      {/* Custom Confirmation Modal */}
      <Modal isOpen={isOpen} onOpenChange={onOpenChange} backdrop="blur">
        <ModalContent>
          {(onClose) => (
            <>
              <ModalHeader className="flex flex-col gap-1 items-center pt-8">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${actionType === 'Approve' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                  {actionType === 'Approve' ? <Check size={32} /> : <AlertTriangle size={32} />}
                </div>
                <h2 className="text-xl font-bold">{actionType} Leave Request?</h2>
              </ModalHeader>
              <ModalBody className="text-center pb-6">
                <p className="text-default-500">
                  You are about to {actionType.toLowerCase()} {selectedRequest?.duration} days of {selectedRequest?.type} for <span className="font-bold">{selectedRequest?.employee_name}</span>.
                </p>
                {actionType === 'Reject' && (
                  <div className="mt-4 p-3 bg-warning/10 border border-warning/20 rounded-xl text-warning-700 text-sm font-medium flex items-start gap-3 text-left">
                    <AlertTriangle size={18} className="shrink-0 mt-0.5" />
                    <p>Pro Tip: When rejecting a leave, it is best practice to add a comment explaining the rejection for the employee's visibility.</p>
                  </div>
                )}
              </ModalBody>
              <ModalFooter className="flex justify-center gap-4 pb-8">
                <Button variant="light" onPress={onClose} className="font-bold w-32">
                  Cancel
                </Button>
                <Button 
                  color={actionType === 'Approve' ? 'success' : 'danger'}
                  onPress={handleAction}
                  isLoading={actionMutation.isPending}
                  className="font-bold w-32 shadow-lg"
                >
                  Confirm {actionType}
                </Button>
              </ModalFooter>
            </>
          )}
        </ModalContent>
      </Modal>

    </div>
  );
}
