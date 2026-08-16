"use client";

import React from "react";
import Link from "next/link";
import { useArtifacts } from "@/hooks/useArtifacts";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import { formatFileSize, formatDate } from "@/lib/utils/formatters";
import { DOCUMENT_TYPE_LABELS } from "@/lib/utils/constants";
import { FileUp, FolderOpen, FileText, ArrowRight } from "lucide-react";

export function RecentDocuments() {
  const { data: artifacts, isLoading } = useArtifacts();

  const recentArtifacts = (artifacts || []).slice(0, 5);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4 animate-pulse">
        <div className="h-5 w-40 rounded bg-slate-800" />
        <div className="h-16 rounded-lg bg-slate-800" />
        <div className="h-16 rounded-lg bg-slate-800" />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
        <div>
          <h3 className="text-base font-semibold text-white">Recent Documents</h3>
          <p className="text-xs text-slate-400">
            Recently uploaded resumes, certificates, marksheets, and reports
          </p>
        </div>
        <Link
          href="/documents"
          className="text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
        >
          View all →
        </Link>
      </div>

      {recentArtifacts.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 border border-slate-800 text-slate-500 mb-3 shadow-inner">
            <FolderOpen className="h-6 w-6" />
          </div>
          <h4 className="text-sm font-semibold text-slate-200">
            No documents uploaded yet
          </h4>
          <p className="mt-1 text-xs text-slate-400 max-w-sm">
            Your uploaded career artifacts and extraction results will appear here.
          </p>
          <Link
            href="/documents"
            className="mt-4 inline-flex items-center space-x-2 rounded-lg bg-emerald-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500 transition-colors"
          >
            <FileUp className="h-3.5 w-3.5" />
            <span>Upload Document</span>
          </Link>
        </div>
      ) : (
        /* List of Recent Artifacts */
        <div className="divide-y divide-slate-800/60">
          {recentArtifacts.map((artifact) => {
            const documentTypeDisplay = artifact.document_type
              ? DOCUMENT_TYPE_LABELS[artifact.document_type] || artifact.document_type
              : artifact.status === "completed"
              ? "Unclassified"
              : "Classifying...";

            return (
              <div
                key={artifact.id}
                className="flex items-center justify-between py-3 group hover:bg-slate-900/60 rounded-lg px-2 transition-colors"
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-800 border border-slate-700/60 text-emerald-400">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <Link href={`/documents/${artifact.id}`}>
                      <p className="truncate text-sm font-medium text-white group-hover:text-emerald-300 transition-colors">
                        {artifact.filename}
                      </p>
                    </Link>
                    <p className="text-xs text-slate-400">
                      {documentTypeDisplay} • {formatFileSize(artifact.file_size)} •{" "}
                      {formatDate(artifact.created_at)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0 ml-2">
                  <DocumentStatusBadge status={artifact.status} />
                  <Link
                    href={`/documents/${artifact.id}`}
                    className="text-slate-400 hover:text-emerald-400 transition-colors"
                  >
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default RecentDocuments;
