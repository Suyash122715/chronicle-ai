"use client";

import React, { useState } from "react";
import { ProvenanceItem } from "@/types/extraction";
import { ChevronDown, ChevronRight, FileSearch, Quote, ShieldCheck } from "lucide-react";

interface ProvenanceViewerProps {
  provenance: Record<string, ProvenanceItem>;
}

function formatFieldLabel(key: string): string {
  if (!key) return "";
  return key
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function ProvenanceViewer({ provenance }: ProvenanceViewerProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!provenance || Object.keys(provenance).length === 0) return null;

  const entries = Object.entries(provenance);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 space-y-4">
      {/* Header Accordion Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between border-b border-slate-800/80 pb-3 text-left"
      >
        <div className="flex items-center space-x-2">
          <FileSearch className="h-5 w-5 text-emerald-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Field-Level Provenance & Evidence
          </h3>
          <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-400 border border-slate-700">
            {entries.length} fields
          </span>
        </div>

        <div className="flex items-center space-x-1 text-xs text-slate-400 font-medium">
          <span>{isOpen ? "Hide Evidence" : "View Evidence"}</span>
          {isOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </div>
      </button>

      {/* Expandable Provenance List */}
      {isOpen && (
        <div className="grid gap-3 sm:grid-cols-2 pt-1">
          {entries.map(([fieldKey, item]) => {
            if (!item) return null;

            return (
              <div
                key={fieldKey}
                className="rounded-lg border border-slate-800 bg-slate-900/40 p-3.5 space-y-2 text-xs"
              >
                <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                  <span className="font-semibold text-emerald-400">
                    {formatFieldLabel(fieldKey)}
                  </span>
                  {item.confidence && (
                    <span className="inline-flex items-center space-x-1 text-[10px] font-medium text-slate-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                      <ShieldCheck className="h-3 w-3 text-emerald-400" />
                      <span>{item.confidence}</span>
                    </span>
                  )}
                </div>

                {/* Evidence Snippet */}
                {item.evidence && (
                  <div className="space-y-1">
                    <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center space-x-1">
                      <Quote className="h-3 w-3 text-slate-500" />
                      <span>Source Evidence</span>
                    </span>
                    <blockquote className="rounded bg-slate-950 p-2.5 text-slate-300 italic border-l-2 border-emerald-500/50 break-words leading-relaxed">
                      &quot;{item.evidence}&quot;
                    </blockquote>
                  </div>
                )}

                {/* Source & Extraction Method */}
                <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 pt-1">
                  {item.source && (
                    <span>
                      Location: <strong className="text-slate-200">{item.source}</strong>
                    </span>
                  )}
                  {item.method && (
                    <span>
                      Method: <strong className="text-slate-200">{item.method}</strong>
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ProvenanceViewer;
