"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArtifactResponse } from "@/types/artifact";
import { formatFileSize, formatDate } from "@/lib/utils/formatters";
import { DOCUMENT_TYPE_LABELS } from "@/lib/utils/constants";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import DeleteConfirmModal from "@/components/documents/DeleteConfirmModal";
import { useDeleteArtifact } from "@/hooks/useArtifacts";
import { FileText, Trash2, ArrowRight, Calendar } from "lucide-react";

interface DocumentCardProps {
  artifact: ArtifactResponse;
}

export function DocumentCard({ artifact }: DocumentCardProps) {
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const deleteMutation = useDeleteArtifact();

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(artifact.id);
      setIsDeleteOpen(false);
    } catch {
      // Error handled by mutation state
    }
  };

  const documentTypeDisplay = artifact.document_type
    ? DOCUMENT_TYPE_LABELS[artifact.document_type] || artifact.document_type
    : artifact.status === "completed"
    ? "Unclassified"
    : "Classifying...";

  return (
    <>
      <div className="group relative flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/40 p-5 transition-all duration-200 hover:border-slate-700 hover:bg-slate-900/80 shadow-sm">
        <div className="space-y-3">
          {/* Card Header: Type Badge + Status + Delete */}
          <div className="flex items-center justify-between">
            <span className="rounded bg-slate-800 px-2 py-0.5 text-[11px] font-semibold text-slate-300 border border-slate-700">
              {documentTypeDisplay}
            </span>

            <div className="flex items-center space-x-2">
              <DocumentStatusBadge status={artifact.status} />
              <button
                onClick={() => setIsDeleteOpen(true)}
                className="rounded-lg p-1 text-slate-500 hover:bg-rose-950/40 hover:text-rose-400 transition-colors"
                title="Delete document"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Filename & Details */}
          <div className="flex items-start space-x-3 pt-1">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-800 border border-slate-700/60 text-emerald-400">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <Link href={`/documents/${artifact.id}`}>
                <h4 className="truncate text-sm font-semibold text-white group-hover:text-emerald-300 transition-colors">
                  {artifact.filename}
                </h4>
              </Link>
              <div className="mt-1 flex items-center space-x-3 text-xs text-slate-400">
                <span>{formatFileSize(artifact.file_size)}</span>
                <span>•</span>
                <span className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3 text-slate-500" />
                  <span>{formatDate(artifact.created_at)}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Error Banner if failed */}
          {artifact.status === "failed" && artifact.error_message && (
            <p className="rounded bg-rose-950/40 p-2 text-xs text-rose-300 border border-rose-900/40 truncate">
              {artifact.error_message}
            </p>
          )}
        </div>

        {/* Action Link Footer */}
        <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between">
          <span className="text-[11px] font-mono text-slate-500">
            ID: {artifact.id.slice(0, 8)}...
          </span>

          <Link
            href={`/documents/${artifact.id}`}
            className="inline-flex items-center text-xs font-semibold text-emerald-400 hover:text-emerald-300 transition-colors"
          >
            <span>Details</span>
            <ArrowRight className="ml-1 h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
          </Link>
        </div>
      </div>

      <DeleteConfirmModal
        isOpen={isDeleteOpen}
        filename={artifact.filename}
        isLoading={deleteMutation.isPending}
        onConfirm={handleDelete}
        onCancel={() => setIsDeleteOpen(false)}
      />
    </>
  );
}

export default DocumentCard;
