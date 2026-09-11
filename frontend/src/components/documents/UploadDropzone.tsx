"use client";

import React, { useState, useRef } from "react";
import { useUploadArtifact } from "@/hooks/useArtifacts";
import { ALLOWED_MIME_TYPES, MAX_UPLOAD_SIZE_BYTES } from "@/lib/utils/constants";
import { formatFileSize } from "@/lib/utils/formatters";
import { ApiError } from "@/types/api";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { UploadCloud, File, X } from "lucide-react";
import { clsx } from "clsx";

interface UploadDropzoneProps {
  onSuccess?: () => void;
}

export function UploadDropzone({ onSuccess }: UploadDropzoneProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadArtifact();

  const validateFile = (file: File): boolean => {
    setValidationError(null);
    setSuccessMessage(null);

    // 1. File Size Validation
    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      setValidationError(
        `File size (${formatFileSize(file.size)}) exceeds the maximum allowed limit of ${formatFileSize(MAX_UPLOAD_SIZE_BYTES)}.`
      );
      return false;
    }

    // 2. MIME Type Validation
    if (file.type && !ALLOWED_MIME_TYPES.includes(file.type)) {
      setValidationError(
        `Unsupported file type (${file.type || "unknown"}). Allowed formats: PDF, PNG, JPG, JPEG, TXT, DOC, DOCX.`
      );
      return false;
    }

    return true;
  };

  const handleFileSelect = (file: File) => {
    if (validateFile(file)) {
      setSelectedFile(file);
    } else {
      setSelectedFile(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const res = await uploadMutation.mutateAsync(selectedFile);
      setSuccessMessage(res.message || "Artifact uploaded successfully.");
      setSelectedFile(null);
      if (onSuccess) onSuccess();
    } catch {
      // Error is handled via mutation state or ApiError
    }
  };

  const errorMessage =
    validationError ||
    (uploadMutation.error instanceof ApiError
      ? uploadMutation.error.detail
      : uploadMutation.error?.message);

  return (
    <div className="space-y-4">
      {errorMessage && <Alert variant="error" message={errorMessage} />}
      {successMessage && <Alert variant="success" message={successMessage} />}

      {/* Drag and Drop Zone */}
      {!selectedFile ? (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={clsx(
            "flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-200",
            isDragOver
              ? "border-emerald-500 bg-emerald-950/20"
              : "border-slate-800 bg-slate-900/30 hover:border-slate-700 hover:bg-slate-900/60"
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg,.txt,.doc,.docx"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
              }
            }}
          />

          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 border border-slate-800 text-emerald-400 mb-3 shadow-inner">
            <UploadCloud className="h-6 w-6" />
          </div>

          <h4 className="text-sm font-semibold text-slate-200">
            Click to upload or drag & drop file
          </h4>
          <p className="mt-1 text-xs text-slate-400">
            Supported formats: PDF, PNG, JPG, JPEG, TXT, DOC, DOCX (Max 10 MB)
          </p>
        </div>
      ) : (
        /* Selected File Preview Box */
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <File className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-white">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-slate-400">
                  {formatFileSize(selectedFile.size)} • {selectedFile.type || "Document"}
                </p>
              </div>
            </div>

            <button
              onClick={() => setSelectedFile(null)}
              disabled={uploadMutation.isPending}
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 disabled:opacity-50"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex justify-end space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedFile(null)}
              disabled={uploadMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleUpload}
              isLoading={uploadMutation.isPending}
            >
              Upload Artifact
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default UploadDropzone;
