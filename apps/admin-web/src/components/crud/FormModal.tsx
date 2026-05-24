'use client';

import React from 'react';
import {
  Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, Input, Textarea, Select, SelectItem,
} from '@nextui-org/react';

export type FormField = {
  key: string;
  label: string;
  type?: 'text' | 'number' | 'date' | 'textarea' | 'select';
  options?: { value: string; label: string }[];
  required?: boolean;
};

type FormModalProps = {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  fields: FormField[];
  formData: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onSubmit: () => void;
  isLoading?: boolean;
  submitLabel?: string;
};

export function FormModal({
  isOpen,
  onOpenChange,
  title,
  fields,
  formData,
  onChange,
  onSubmit,
  isLoading,
  submitLabel = 'Save',
}: FormModalProps) {
  return (
    <Modal isOpen={isOpen} onOpenChange={onOpenChange} size="2xl" scrollBehavior="inside">
      <ModalContent>
        {(onClose) => (
          <>
            <ModalHeader>{title}</ModalHeader>
            <ModalBody className="flex flex-col gap-4">
              {fields.map((field) => {
                if (field.type === 'textarea') {
                  return (
                    <Textarea
                      key={field.key}
                      label={field.label}
                      value={formData[field.key] ?? ''}
                      onValueChange={(v) => onChange(field.key, v)}
                      isRequired={field.required}
                    />
                  );
                }
                if (field.type === 'select' && field.options) {
                  return (
                    <Select
                      key={field.key}
                      label={field.label}
                      selectedKeys={formData[field.key] ? [formData[field.key]] : []}
                      onSelectionChange={(keys) => {
                        const val = Array.from(keys)[0] as string;
                        onChange(field.key, val ?? '');
                      }}
                    >
                      {field.options.map((o) => (
                        <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>
                      ))}
                    </Select>
                  );
                }
                return (
                  <Input
                    key={field.key}
                    type={field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'}
                    label={field.label}
                    value={formData[field.key] ?? ''}
                    onValueChange={(v) => onChange(field.key, v)}
                    isRequired={field.required}
                  />
                );
              })}
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onClose}>Cancel</Button>
              <Button color="primary" isLoading={isLoading} onPress={onSubmit}>{submitLabel}</Button>
            </ModalFooter>
          </>
        )}
      </ModalContent>
    </Modal>
  );
}
