"use client";

import React from "react";
import { Network, Link2, Sparkles } from "lucide-react";

interface GraphStatsBarProps {
  totalNodes: number;
  totalEdges: number;
  activeEntityTypes: number;
}

export function GraphStatsBar({ totalNodes, totalEdges, activeEntityTypes }: GraphStatsBarProps) {
  return (
    <div className="flex items-center gap-4 text-xs text-slate-400">
      <div className="flex items-center gap-1.5">
        <Network className="h-3.5 w-3.5 text-emerald-500" />
        <span className="font-semibold text-white">{totalNodes}</span>
        <span>entities</span>
      </div>
      <div className="h-3 w-px bg-slate-700" />
      <div className="flex items-center gap-1.5">
        <Link2 className="h-3.5 w-3.5 text-blue-400" />
        <span className="font-semibold text-white">{totalEdges}</span>
        <span>relationships</span>
      </div>
      <div className="h-3 w-px bg-slate-700" />
      <div className="flex items-center gap-1.5">
        <Sparkles className="h-3.5 w-3.5 text-violet-400" />
        <span className="font-semibold text-white">{activeEntityTypes}</span>
        <span>types</span>
      </div>
    </div>
  );
}

export default GraphStatsBar;
