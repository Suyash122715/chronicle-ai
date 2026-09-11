import React from "react";
import { ExtractionStatus as StatusType, ConfidenceLevel } from "@/types/extraction";
import { formatDateTime } from "@/lib/utils/formatters";
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle, MinusCircle, Cpu, Clock, Tag } from "lucide-react";
import { clsx } from "clsx";

interface ExtractionStatusProps {
  status: StatusType | string;
  confidence: ConfidenceLevel | string;
  extractorVersion: string;
  promptVersion: string;
  startedAt: string;
  completedAt: string;
  llmMetadata?: Record<string, unknown>;
}

export function ExtractionStatus({
  status,
  confidence,
  extractorVersion,
  promptVersion,
  startedAt,
  completedAt,
  llmMetadata,
}: ExtractionStatusProps) {
  const statusConfig = {
    SUCCESS: {
      label: "Success",
      bg: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
      icon: CheckCircle2,
    },
    PARTIAL: {
      label: "Partial",
      bg: "bg-amber-500/10 border-amber-500/20 text-amber-400",
      icon: AlertTriangle,
    },
    FAILED: {
      label: "Failed",
      bg: "bg-rose-500/10 border-rose-500/20 text-rose-400",
      icon: AlertCircle,
    },
    NOT_SUPPORTED: {
      label: "Not Supported",
      bg: "bg-slate-500/10 border-slate-500/20 text-slate-400",
      icon: MinusCircle,
    },
    SKIPPED: {
      label: "Skipped",
      bg: "bg-slate-500/10 border-slate-500/20 text-slate-400",
      icon: HelpCircle,
    },
  };

  const normalizedStatus = (status || "SUCCESS").toUpperCase() as keyof typeof statusConfig;
  const currentStatus = statusConfig[normalizedStatus] || {
    label: String(status),
    bg: "bg-slate-500/10 border-slate-500/20 text-slate-400",
    icon: HelpCircle,
  };
  const StatusIcon = currentStatus.icon;

  const confidenceColor =
    confidence === "HIGH"
      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
      : confidence === "MEDIUM"
      ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
      : "text-slate-400 bg-slate-500/10 border-slate-500/20";

  // Calculate execution latency in milliseconds if timestamps exist
  let durationText = "";
  if (startedAt && completedAt) {
    try {
      const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime();
      if (!isNaN(ms) && ms >= 0) {
        durationText = ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(2)}s`;
      }
    } catch {
      durationText = "";
    }
  }

  const modelName = typeof llmMetadata?.model === "string" ? llmMetadata.model : null;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        {/* Status Badge */}
        <div className="flex items-center space-x-3">
          <span
            className={clsx(
              "inline-flex items-center space-x-1.5 rounded-full border px-3 py-1 text-xs font-semibold select-none",
              currentStatus.bg
            )}
          >
            <StatusIcon className="h-3.5 w-3.5" />
            <span>Extraction {currentStatus.label}</span>
          </span>

          {/* Confidence Badge */}
          <span
            className={clsx(
              "inline-flex items-center space-x-1 rounded-full border px-2.5 py-0.5 text-[11px] font-medium",
              confidenceColor
            )}
          >
            <span>Confidence: {confidence}</span>
          </span>
        </div>

        {/* Latency */}
        {durationText && (
          <div className="flex items-center space-x-1 text-xs font-mono text-slate-400">
            <Clock className="h-3.5 w-3.5 text-slate-500" />
            <span>Duration: {durationText}</span>
          </div>
        )}
      </div>

      {/* Grid Metadata Items */}
      <div className="grid gap-3 sm:grid-cols-3 text-xs">
        <div className="flex items-center space-x-2 text-slate-300">
          <Cpu className="h-4 w-4 text-emerald-400 shrink-0" />
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-semibold tracking-wider">
              Extractor
            </span>
            <span className="font-mono text-slate-200">
              {extractorVersion} {modelName ? `(${modelName})` : ""}
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-slate-300">
          <Tag className="h-4 w-4 text-emerald-400 shrink-0" />
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-semibold tracking-wider">
              Prompt Version
            </span>
            <span className="font-mono text-slate-200">{promptVersion}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-slate-300">
          <Clock className="h-4 w-4 text-emerald-400 shrink-0" />
          <div>
            <span className="text-slate-500 block text-[10px] uppercase font-semibold tracking-wider">
              Completed At
            </span>
            <span className="text-slate-200">{formatDateTime(completedAt)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ExtractionStatus;
