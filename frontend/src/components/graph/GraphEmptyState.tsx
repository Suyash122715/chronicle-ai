"use client";

import React from "react";
import { Network } from "lucide-react";

interface GraphEmptyStateProps {
  hasFilters: boolean;
  onReset: () => void;
}

export function GraphEmptyState({ hasFilters, onReset }: GraphEmptyStateProps) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-5 text-center px-8">
      <div className="relative">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-slate-900 border border-slate-800">
          <Network className="h-9 w-9 text-slate-600" />
        </div>
        {/* decorative orbit dots */}
        <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-emerald-500/50 animate-pulse" />
        <span className="absolute -bottom-1 -left-1 h-2 w-2 rounded-full bg-blue-500/40 animate-pulse delay-500" />
      </div>

      <div className="space-y-2">
        {hasFilters ? (
          <>
            <h3 className="text-base font-semibold text-white">No matches for this filter</h3>
            <p className="text-sm text-slate-400 max-w-xs">
              No entities or relationships match the selected filters. Try adjusting or clearing them.
            </p>
            <button
              onClick={onReset}
              className="mt-3 rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white"
            >
              Clear filters
            </button>
          </>
        ) : (
          <>
            <h3 className="text-base font-semibold text-white">Knowledge graph is empty</h3>
            <p className="text-sm text-slate-400 max-w-xs">
              Upload and process documents to start building your career knowledge graph. Entities and
              relationships will appear here automatically.
            </p>
          </>
        )}
      </div>
    </div>
  );
}

export default GraphEmptyState;
