"use client";

import React, { use } from "react";
import Link from "next/link";
import { useArtifact } from "@/hooks/useArtifacts";
import DocumentStatusBadge from "@/components/documents/DocumentStatusBadge";
import ExtractionViewer from "@/components/extraction/ExtractionViewer";
import { formatFileSize, formatDateTime } from "@/lib/utils/formatters";
import { DOCUMENT_TYPE_LABELS } from "@/lib/utils/constants";
import { Alert } from "@/components/ui/Alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import {
  ArrowLeft,
  FileText,
  Clock,
  Layers,
} from "lucide-react";

interface DocumentDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function DocumentDetailPage({ params }: DocumentDetailPageProps) {
  const resolvedParams = use(params);
  const artifactId = resolvedParams.id;

  const { data: artifact, isLoading, isError, error } = useArtifact(artifactId);

  // ── Loading State ────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-5 w-28 rounded bg-slate-800" />
        <div className="h-20 rounded-xl border border-slate-800 bg-slate-900/30" />
        <div className="grid gap-6 md:grid-cols-2">
          <div className="h-48 rounded-xl border border-slate-800 bg-slate-900/30" />
          <div className="h-48 rounded-xl border border-slate-800 bg-slate-900/30" />
        </div>
        <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/30" />
      </div>
    );
  }

  // ── Error / Not Found State ──────────────────────────────────────────
  if (isError || !artifact) {
    return (
      <div className="space-y-4">
        <Link
          href="/documents"
          className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Documents</span>
        </Link>
        <Alert
          variant="error"
          message={
            error?.message || "Artifact not found or you do not have permission to view it."
          }
        />
      </div>
    );
  }

  const documentTypeDisplay = artifact.document_type
    ? DOCUMENT_TYPE_LABELS[artifact.document_type] || artifact.document_type
    : artifact.status === "completed"
    ? "Unclassified"
    : "Classifying...";

  // ── Main Page ────────────────────────────────────────────────────────
  return (
    <div className="space-y-8">
      {/* Back Navigation */}
      <Link
        href="/documents"
        className="inline-flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Back to Documents</span>
      </Link>

      {/* ── Document Header ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="flex items-start space-x-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <FileText className="h-6 w-6" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
              <h2 className="text-2xl font-bold tracking-tight text-white">
                {artifact.filename}
              </h2>
              <DocumentStatusBadge status={artifact.status} />
            </div>
            <p className="mt-1 text-xs font-mono text-slate-500">ID: {artifact.id}</p>
          </div>
        </div>
      </div>

      {/* Upload-failed error alert */}
      {artifact.status === "failed" && artifact.error_message && (
        <Alert
          variant="error"
          message={`Processing failed: ${artifact.error_message}`}
        />
      )}

      {/* ── Document Information ─────────────────────────────────────── */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Classification & Metadata Card */}
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <Layers className="h-5 w-5 text-emerald-400" />
              <span>Classification &amp; Metadata</span>
            </CardTitle>
            <CardDescription>Deterministic document classification results</CardDescription>
          </CardHeader>
          <CardContent className="space-y-0 text-sm divide-y divide-slate-800/60">
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">Document Type</span>
              <span className="font-semibold text-emerald-400">{documentTypeDisplay}</span>
            </div>
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">Classification Confidence</span>
              <span className="font-medium text-slate-200">
                {artifact.classification_confidence || "N/A"}
              </span>
            </div>
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">Classifier Version</span>
              <span className="font-mono text-xs text-slate-300">
                {artifact.classifier_version || "N/A"}
              </span>
            </div>
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">File Size</span>
              <span className="font-medium text-slate-200">
                {formatFileSize(artifact.file_size)}
              </span>
            </div>
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">MIME Type</span>
              <span className="font-mono text-xs text-slate-300">{artifact.mime_type}</span>
            </div>
          </CardContent>
        </Card>

        {/* Timestamps & Lifecycle Card */}
        <Card className="border-slate-800 bg-slate-900/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <Clock className="h-5 w-5 text-emerald-400" />
              <span>Processing Lifecycle</span>
            </CardTitle>
            <CardDescription>Pipeline timestamp log</CardDescription>
          </CardHeader>
          <CardContent className="space-y-0 text-sm divide-y divide-slate-800/60">
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">Uploaded At</span>
              <span className="font-medium text-slate-200">
                {formatDateTime(artifact.created_at)}
              </span>
            </div>
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">Classified At</span>
              <span className="font-medium text-slate-200">
                {formatDateTime(artifact.classified_at)}
              </span>
            </div>
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">Last Updated</span>
              <span className="font-medium text-slate-200">
                {formatDateTime(artifact.updated_at)}
              </span>
            </div>
            <div className="flex justify-between py-2.5">
              <span className="text-slate-400">Retry Count</span>
              <span className="font-mono text-xs text-slate-300">{artifact.retry_count}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Raw Extracted Text */}
      {artifact.raw_text && (
        <Card className="border-slate-800 bg-slate-900/40">
          <CardHeader>
            <CardTitle className="text-base">Extracted Raw Text</CardTitle>
            <CardDescription>Text extracted during artifact preprocessing</CardDescription>
          </CardHeader>
          <CardContent>
            <pre className="max-h-60 overflow-y-auto rounded-lg bg-slate-950 p-4 font-mono text-xs text-slate-300 border border-slate-800 whitespace-pre-wrap leading-relaxed">
              {artifact.raw_text}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* ── Extraction Results ───────────────────────────────────────── */}
      <ExtractionViewer artifact={artifact} />
    </div>
  );
}
