'use client';

import React, { useState } from 'react';
import {
  Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Button, Input, Textarea, Select, SelectItem,
} from '@nextui-org/react';
import { validateRequired } from '@/lib/validation';

export type FormField = {
  key: string;
  label: string;
  type?: 'text' | 'number' | 'date' | 'textarea' | 'select';
  options?: { value: string; label: string }[];
  required?: boolean;
  maxLength?: number;
  validate?: (value: string) => string | undefined;
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
  isDisabled?: boolean;
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
  isDisabled,
  submitLabel = 'Save',
}: FormModalProps) {
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSubmit = () => {
    const next: Record<string, string> = {};
    fields.forEach((field) => {
      const value = formData[field.key] ?? '';
      if (field.validate) {
        const err = field.validate(value);
        if (err) next[field.key] = err;
      } else if (field.required) {
        const err = validateRequired(value, field.label);
        if (err) next[field.key] = err;
      }
    });
    if (Object.keys(next).length) {
      setFieldErrors(next);
      return;
    }
    setFieldErrors({});
    onSubmit();
  };

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
                    maxLength={field.maxLength}
                    errorMessage={fieldErrors[field.key]}
                    isInvalid={!!fieldErrors[field.key]}
                  />
                );
              })}
            </ModalBody>
            <ModalFooter>
              <Button variant="light" onPress={onClose}>Cancel</Button>
              <Button
                color="primary"
                isLoading={isLoading}
                isDisabled={isDisabled || isLoading}
                onPress={handleSubmit}
              >
                {submitLabel}
              </Button>
            </ModalFooter>
          </>
        )}
      </ModalContent>
    </Modal>
  );
}
