"use client";

import React from "react";
import { Button } from "@/components/ui/Button";
import { AlertTriangle } from "lucide-react";

interface DeleteConfirmModalProps {
  isOpen: boolean;
  filename: string;
  isLoading: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeleteConfirmModal({
  isOpen,
  filename,
  isLoading,
  onConfirm,
  onCancel,
}: DeleteConfirmModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={onCancel}
      />

      {/* Modal Card */}
      <div className="relative z-50 w-full max-w-md rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-4">
        <div className="flex items-center space-x-3 text-rose-400">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-950/50 border border-rose-900/50">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <h3 className="text-lg font-bold text-white">Delete Artifact</h3>
        </div>

        <p className="text-sm text-slate-300">
          Are you sure you want to delete <span className="font-semibold text-white">&quot;{filename}&quot;</span>? This action will permanently remove the record and physical file storage.
        </p>

        <div className="flex justify-end space-x-3 pt-2">
          <Button variant="outline" size="sm" onClick={onCancel} disabled={isLoading}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" onClick={onConfirm} isLoading={isLoading}>
            Delete Permanently
          </Button>
        </div>
      </div>
    </div>
  );
}

export default DeleteConfirmModal;
