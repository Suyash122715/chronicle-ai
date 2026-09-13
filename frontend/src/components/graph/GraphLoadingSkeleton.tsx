"use client";

import React from "react";

export function GraphLoadingSkeleton() {
  return (
    <div className="relative h-full w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-950">
      {/* Animated shimmer background */}
      <div className="absolute inset-0 animate-pulse bg-gradient-to-br from-slate-950 via-slate-900/60 to-slate-950" />

      {/* Mock nodes scattered around */}
      {[
        { top: "20%", left: "15%", w: "w-20", h: "h-20" },
        { top: "15%", left: "55%", w: "w-24", h: "h-24" },
        { top: "55%", left: "25%", w: "w-16", h: "h-16" },
        { top: "60%", left: "65%", w: "w-20", h: "h-20" },
        { top: "35%", left: "75%", w: "w-14", h: "h-14" },
        { top: "75%", left: "45%", w: "w-18", h: "h-18" },
      ].map((pos, i) => (
        <div
          key={i}
          className={`absolute ${pos.w} ${pos.h} rounded-full border border-slate-700/40 bg-slate-800/40 animate-pulse`}
          style={{ top: pos.top, left: pos.left, animationDelay: `${i * 150}ms` }}
        />
      ))}

      {/* Loading label */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-1.5 w-24 rounded-full bg-emerald-500/30 animate-pulse" />
          <p className="text-xs text-slate-500 animate-pulse">Loading graph…</p>
        </div>
      </div>
    </div>
  );
}

export default GraphLoadingSkeleton;
