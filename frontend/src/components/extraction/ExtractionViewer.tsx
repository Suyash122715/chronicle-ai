"use client";

import React from "react";
import { useExtraction } from "@/hooks/useExtraction";
import { ExtractionStatus } from "@/components/extraction/ExtractionStatus";
import { StructuredDataViewer } from "@/components/extraction/StructuredDataViewer";
import { ProvenanceViewer } from "@/components/extraction/ProvenanceViewer";
import { ExtractionWarnings } from "@/components/extraction/ExtractionWarnings";
import { ArtifactResponse } from "@/types/artifact";
import { Alert } from "@/components/ui/Alert";
import { ApiError } from "@/types/api";
import {
  Sparkles,
  Loader2,
  Clock,
  AlertCircle,
  MinusCircle,
  SkipForward,
} from "lucide-react";

interface ExtractionViewerProps {
  artifact: ArtifactResponse;
}

// Skeleton loader for extraction panel
function ExtractionSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-24 rounded-xl border border-slate-800 bg-slate-900/40" />
      <div className="h-64 rounded-xl border border-slate-800 bg-slate-900/40" />
      <div className="h-32 rounded-xl border border-slate-800 bg-slate-900/40" />
    </div>
  );
}

// State: artifact still being processed — no point fetching extraction yet
function ArtifactProcessingState({ status }: { status: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/30 py-12 px-8 text-center space-y-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-800 border border-slate-700">
        <Loader2 className="h-7 w-7 text-emerald-400 animate-spin" />
      </div>
      <div className="space-y-1.5">
        <h3 className="text-base font-semibold text-white">Document is Being Processed</h3>
        <p className="text-sm text-slate-400 max-w-md">
          {status === "pending"
            ? "Your document is queued for processing. Extraction results will be available once processing is complete."
            : "Your document is currently being processed by the AI pipeline. Extraction results will appear here automatically once complete."}
        </p>
      </div>
      <span className="inline-flex items-center space-x-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 px-3 py-1 text-xs font-medium text-amber-400">
        <Clock className="h-3.5 w-3.5" />
        <span>Status: {status.charAt(0).toUpperCase() + status.slice(1)}</span>
      </span>
    </div>
  );
}

// State: 404 — extraction record not yet created
function NoExtractionYetState({ artifactStatus }: { artifactStatus: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-slate-900/30 py-12 px-8 text-center space-y-4">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-800 border border-slate-700">
        <Sparkles className="h-7 w-7 text-slate-400" />
      </div>
      <div className="space-y-1.5">
        <h3 className="text-base font-semibold text-white">Extraction Not Yet Available</h3>
        <p className="text-sm text-slate-400 max-w-md">
          {artifactStatus === "completed"
            ? "This document has been processed but no extraction record was found. This may indicate that extraction was skipped or is not applicable for this document type."
            : "Extraction will begin after the document has finished processing."}
        </p>
      </div>
    </div>
  );
}

// State: FAILED extraction
function ExtractionFailedState({ errorMessage }: { errorMessage: string | null }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-rose-900/50 bg-rose-950/20 py-10 px-8 text-center space-y-3">
      <AlertCircle className="h-10 w-10 text-rose-400" />
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-rose-300">Extraction Failed</h3>
        {errorMessage && (
          <p className="text-xs text-rose-400/80 max-w-md break-words">{errorMessage}</p>
        )}
        {!errorMessage && (
          <p className="text-xs text-rose-400/80">
            The extraction pipeline encountered an error. Check the document status for more details.
          </p>
        )}
      </div>
    </div>
  );
}

// State: NOT_SUPPORTED
function NotSupportedState({ errorMessage }: { errorMessage: string | null }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-slate-700/60 bg-slate-900/30 py-10 px-8 text-center space-y-3">
      <MinusCircle className="h-10 w-10 text-slate-500" />
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-slate-300">Extraction Not Supported</h3>
        <p className="text-xs text-slate-400 max-w-md">
          {errorMessage ||
            "Structured extraction is not supported for this document type. Classification metadata is still available above."}
        </p>
      </div>
    </div>
  );
}

// State: SKIPPED
function SkippedState({ errorMessage }: { errorMessage: string | null }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-slate-700/60 bg-slate-900/30 py-10 px-8 text-center space-y-3">
      <SkipForward className="h-10 w-10 text-slate-500" />
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-slate-300">Extraction Skipped</h3>
        <p className="text-xs text-slate-400 max-w-md">
          {errorMessage || "Extraction was skipped for this document."}
        </p>
      </div>
    </div>
  );
}

export function ExtractionViewer({ artifact }: ExtractionViewerProps) {
  // Only fetch extraction when artifact is in a terminal state
  const artifactIsTerminal =
    artifact.status === "completed" || artifact.status === "failed";

  const {
    data: extraction,
    isLoading,
    isError,
    error,
  } = useExtraction(artifact.id, artifactIsTerminal);

  const isApiError = error instanceof ApiError;
  const is404 = isApiError && (error as ApiError).status === 404;

  // ── Section Header ──────────────────────────────────────────────────
  return (
    <section className="space-y-4" aria-label="Extraction Results">
      {/* Section Title */}
      <div className="flex items-center space-x-3 border-b border-slate-800 pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <Sparkles className="h-5 w-5 text-emerald-400" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white tracking-tight">Extraction Results</h3>
          <p className="text-xs text-slate-400">AI-powered structured entity extraction</p>
        </div>
      </div>

      {/* Artifact still pending/processing → skip fetch entirely */}
      {!artifactIsTerminal && (
        <ArtifactProcessingState status={artifact.status} />
      )}

      {/* Extraction data loading */}
      {artifactIsTerminal && isLoading && <ExtractionSkeleton />}

      {/* 404 → no extraction record */}
      {artifactIsTerminal && !isLoading && is404 && (
        <NoExtractionYetState artifactStatus={artifact.status} />
      )}

      {/* Other non-404 fetch error */}
      {artifactIsTerminal && !isLoading && isError && !is404 && (
        <Alert
          variant="error"
          message={
            isApiError
              ? (error as ApiError).message
              : "Failed to load extraction results. Please try refreshing the page."
          }
        />
      )}

      {/* Extraction data loaded — branch by status */}
      {artifactIsTerminal && !isLoading && !isError && extraction && (
        <div className="space-y-4">
          {/* 1. Status Row — always shown */}
          <ExtractionStatus
            status={extraction.status}
            confidence={extraction.confidence}
            extractorVersion={extraction.extractor_version}
            promptVersion={extraction.prompt_version}
            startedAt={extraction.started_at}
            completedAt={extraction.completed_at}
            llmMetadata={extraction.llm_metadata}
          />

          {/* 2. Warnings — shown for SUCCESS, PARTIAL; not for FAILED/SKIPPED/NOT_SUPPORTED */}
          <ExtractionWarnings warnings={extraction.warnings} />

          {/* 3. Specific State Views for non-happy-path statuses */}
          {extraction.status === "FAILED" && (
            <ExtractionFailedState errorMessage={extraction.error_message} />
          )}

          {extraction.status === "NOT_SUPPORTED" && (
            <NotSupportedState errorMessage={extraction.error_message} />
          )}

          {extraction.status === "SKIPPED" && (
            <SkippedState errorMessage={extraction.error_message} />
          )}

          {/* 4. Structured Data — SUCCESS and PARTIAL */}
          {(extraction.status === "SUCCESS" || extraction.status === "PARTIAL") &&
            extraction.structured_data &&
            Object.keys(extraction.structured_data).length > 0 && (
              <StructuredDataViewer data={extraction.structured_data} />
            )}

          {/* 5. Provenance — shown when data is present */}
          {extraction.provenance && Object.keys(extraction.provenance).length > 0 && (
            <ProvenanceViewer provenance={extraction.provenance} />
          )}
        </div>
      )}
    </section>
  );
}

export default ExtractionViewer;
