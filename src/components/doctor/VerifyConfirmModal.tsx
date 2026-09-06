'use client';

import React from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { CheckCircle2, ShieldCheck, AlertCircle } from 'lucide-react';

interface VerifyConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isVerifying: boolean;
  patientName?: string;
  patientId?: string;
}

export const VerifyConfirmModal: React.FC<VerifyConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isVerifying,
  patientName,
  patientId,
}) => {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        <div className="flex items-center gap-2 text-emerald-800">
          <ShieldCheck className="w-5 h-5 text-emerald-600" />
          <span>Confirm Clinical Verification</span>
        </div>
      }
      maxWidth="md"
    >
      <div className="space-y-4">
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-950 leading-relaxed font-medium">
          <p className="font-bold text-sm text-emerald-900 mb-1">
            Doctor Verification Checklist
          </p>
          <p>
            Have you reviewed the AI-assisted summary and made any required corrections for{' '}
            <strong>{patientName || 'this patient'}</strong> (#{patientId})?
          </p>
        </div>

        <p className="text-xs text-slate-600 leading-relaxed">
          Clicking <strong>Verify Summary</strong> will mark this intake record as officially verified by{' '}
          <strong>Dr. Demo</strong> and store the verification timestamp in the permanent clinical audit log.
        </p>

        <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
          <Button
            type="button"
            variant="outline"
            size="md"
            onClick={onClose}
            disabled={isVerifying}
            className="rounded-xl font-semibold"
            id="cancel-verify-btn"
          >
            Cancel
          </Button>

          <Button
            type="button"
            variant="success"
            size="md"
            onClick={onConfirm}
            isLoading={isVerifying}
            leftIcon={<CheckCircle2 className="w-4 h-4 text-white" />}
            className="rounded-xl font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md"
            id="confirm-verify-btn"
          >
            Verify Summary
          </Button>
        </div>
      </div>
    </Modal>
  );
};
