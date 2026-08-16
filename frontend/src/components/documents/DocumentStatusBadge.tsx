import React from "react";
import { ProcessingStatus } from "@/types/artifact";
import { Loader2, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import { clsx } from "clsx";

interface DocumentStatusBadgeProps {
  status: ProcessingStatus | string;
  className?: string;
}

export function DocumentStatusBadge({ status, className }: DocumentStatusBadgeProps) {
  const config = {
    pending: {
      label: "Pending",
      bg: "bg-amber-500/10 border-amber-500/20 text-amber-400",
      icon: Clock,
      animate: false,
    },
    processing: {
      label: "Processing",
      bg: "bg-sky-500/10 border-sky-500/20 text-sky-400",
      icon: Loader2,
      animate: true,
    },
    completed: {
      label: "Completed",
      bg: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
      icon: CheckCircle2,
      animate: false,
    },
    failed: {
      label: "Failed",
      bg: "bg-rose-500/10 border-rose-500/20 text-rose-400",
      icon: AlertCircle,
      animate: false,
    },
  };

  const normalizedStatus = (status || "pending").toLowerCase() as keyof typeof config;
  const item = config[normalizedStatus] || config.pending;
  const Icon = item.icon;

  return (
    <span
      className={clsx(
        "inline-flex items-center space-x-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold select-none",
        item.bg,
        className
      )}
    >
      <Icon className={clsx("h-3.5 w-3.5", item.animate && "animate-spin")} />
      <span>{item.label}</span>
    </span>
  );
}

export default DocumentStatusBadge;
