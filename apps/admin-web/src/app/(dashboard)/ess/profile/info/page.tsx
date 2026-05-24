'use client';

import React, { useEffect, useState } from 'react';
import {
  Card,
  CardBody,
  CardHeader,
  Input,
  Button,
  Spinner,
  Divider,
} from '@nextui-org/react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { employeesApi } from '@/lib/hrmsApi';
import {
  EMPLOYEE_ME_QUERY_KEY,
  EmployeeMeContact,
  EmployeeMeProfile,
} from '@/lib/employeeMe';
import { useAuthReady } from '@/lib/AuthProvider';
import { parseApiError } from '@/lib/parseApiError';

function ReadOnlyField({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-semibold text-default-500 uppercase tracking-wide">{label}</span>
      <span className="text-sm text-foreground">{value || '—'}</span>
    </div>
  );
}

export default function PersonalInfoPage() {
  const isAuthReady = useAuthReady();
  const queryClient = useQueryClient();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [contact, setContact] = useState<Partial<EmployeeMeContact>>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: [EMPLOYEE_ME_QUERY_KEY],
    enabled: isAuthReady,
    queryFn: async () => {
      const res = await employeesApi.me.get();
      return res.data as EmployeeMeProfile;
    },
  });

  useEffect(() => {
    if (!data) return;
    setFirstName(data.user.first_name ?? '');
    setLastName(data.user.last_name ?? '');
    setPhone(data.user.phone_number ?? '');
    if (data.contact) {
      setContact(data.contact);
    } else if (data.has_employee) {
      setContact({
        mobile_number: '',
        present_address: '',
        permanent_address: '',
        emergency_contact_name: '',
        emergency_contact_number: '',
      });
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const payload: Record<string, unknown> = {
        first_name: firstName,
        last_name: lastName,
        phone_number: phone,
      };
      if (data?.has_employee) {
        payload.contact = contact;
      }
      return employeesApi.me.update(payload);
    },
    onSuccess: () => {
      setSaveError(null);
      setSaved(true);
      queryClient.invalidateQueries({ queryKey: [EMPLOYEE_ME_QUERY_KEY] });
      setTimeout(() => setSaved(false), 3000);
    },
    onError: (err) => setSaveError(parseApiError(err, 'Failed to save')),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-danger">
        {error ? parseApiError(error, 'Failed to load profile') : 'Profile not available.'}
      </div>
    );
  }

  const emp = data.employee;

  return (
    <div className="max-w-3xl mx-auto p-6 md:p-8 flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Personal Info</h1>
        <p className="text-default-500 text-sm mt-1">Your account and contact details</p>
      </div>

      <Card className="border border-divider/40">
        <CardHeader className="pb-0">
          <h2 className="text-lg font-semibold">Account</h2>
        </CardHeader>
        <CardBody className="gap-4">
          <ReadOnlyField label="Email" value={data.user.email} />
          <ReadOnlyField label="Username" value={data.user.username} />
          <Input label="First name" value={firstName} onValueChange={setFirstName} variant="bordered" />
          <Input label="Last name" value={lastName} onValueChange={setLastName} variant="bordered" />
          <Input label="Phone" value={phone} onValueChange={setPhone} variant="bordered" />
        </CardBody>
      </Card>

      {emp ? (
        <Card className="border border-divider/40">
          <CardHeader className="pb-0">
            <h2 className="text-lg font-semibold">Employment (read-only)</h2>
          </CardHeader>
          <CardBody className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <ReadOnlyField label="Employee code" value={emp.employee_code} />
            <ReadOnlyField label="Status" value={emp.status} />
            <ReadOnlyField label="Department" value={emp.department_name} />
            <ReadOnlyField label="Designation" value={emp.designation_name} />
            <ReadOnlyField label="Branch" value={emp.branch_name} />
            <ReadOnlyField label="Date of joining" value={emp.date_of_joining} />
          </CardBody>
        </Card>
      ) : (
        <Card className="border border-divider/40 bg-default-50/30">
          <CardBody>
            <p className="text-default-500 text-sm">
              No HR employee profile is linked to this account. Contact your administrator if you
              expect employment details here.
            </p>
          </CardBody>
        </Card>
      )}

      {data.has_employee && (
        <Card className="border border-divider/40">
          <CardHeader className="pb-0">
            <h2 className="text-lg font-semibold">Contact</h2>
          </CardHeader>
          <CardBody className="gap-4">
            <Input
              label="Personal email"
              value={contact.personal_email ?? ''}
              onValueChange={(v) => setContact((c) => ({ ...c, personal_email: v }))}
              variant="bordered"
            />
            <Input
              label="Mobile"
              value={contact.mobile_number ?? ''}
              onValueChange={(v) => setContact((c) => ({ ...c, mobile_number: v }))}
              variant="bordered"
            />
            <Input
              label="Alternate number"
              value={contact.alternate_number ?? ''}
              onValueChange={(v) => setContact((c) => ({ ...c, alternate_number: v }))}
              variant="bordered"
            />
            <Input
              label="Present address"
              value={contact.present_address ?? ''}
              onValueChange={(v) => setContact((c) => ({ ...c, present_address: v }))}
              variant="bordered"
            />
            <Input
              label="Permanent address"
              value={contact.permanent_address ?? ''}
              onValueChange={(v) => setContact((c) => ({ ...c, permanent_address: v }))}
              variant="bordered"
            />
            <Divider />
            <Input
              label="Emergency contact name"
              value={contact.emergency_contact_name ?? ''}
              onValueChange={(v) => setContact((c) => ({ ...c, emergency_contact_name: v }))}
              variant="bordered"
            />
            <Input
              label="Emergency contact number"
              value={contact.emergency_contact_number ?? ''}
              onValueChange={(v) => setContact((c) => ({ ...c, emergency_contact_number: v }))}
              variant="bordered"
            />
          </CardBody>
        </Card>
      )}

      {saveError && <p className="text-danger text-sm">{saveError}</p>}
      {saved && <p className="text-success text-sm">Saved successfully.</p>}

      <Button
        color="primary"
        className="self-start"
        isLoading={saveMutation.isPending}
        onPress={() => saveMutation.mutate()}
      >
        Save changes
      </Button>
    </div>
  );
}
