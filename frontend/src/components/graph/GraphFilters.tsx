"use client";

import React from "react";
import { ENTITY_TYPES } from "@/types/graph";
import { ArtifactResponse } from "@/types/artifact";
import { Filter, X, ChevronDown } from "lucide-react";
import { clsx } from "clsx";

/** Color map for entity type badge dots */
export const ENTITY_TYPE_COLORS: Record<string, { bg: string; border: string; text: string; node: string }> = {
  SKILL:       { bg: "bg-emerald-500/15", border: "border-emerald-500/30", text: "text-emerald-400",  node: "#10b981" },
  PROJECT:     { bg: "bg-blue-500/15",    border: "border-blue-500/30",    text: "text-blue-400",     node: "#3b82f6" },
  COMPANY:     { bg: "bg-violet-500/15",  border: "border-violet-500/30",  text: "text-violet-400",   node: "#8b5cf6" },
  ROLE:        { bg: "bg-amber-500/15",   border: "border-amber-500/30",   text: "text-amber-400",    node: "#f59e0b" },
  TECHNOLOGY:  { bg: "bg-cyan-500/15",    border: "border-cyan-500/30",    text: "text-cyan-400",     node: "#06b6d4" },
  CERTIFICATE: { bg: "bg-rose-500/15",    border: "border-rose-500/30",    text: "text-rose-400",     node: "#f43f5e" },
  INSTITUTION: { bg: "bg-orange-500/15",  border: "border-orange-500/30",  text: "text-orange-400",   node: "#f97316" },
  ACHIEVEMENT: { bg: "bg-yellow-500/15",  border: "border-yellow-500/30",  text: "text-yellow-400",   node: "#eab308" },
};

export const DEFAULT_NODE_COLOR = { bg: "bg-slate-500/15", border: "border-slate-500/30", text: "text-slate-400", node: "#64748b" };

export function getEntityTypeStyle(entityType: string) {
  return ENTITY_TYPE_COLORS[entityType.toUpperCase()] ?? DEFAULT_NODE_COLOR;
}

interface GraphFiltersProps {
  artifacts: ArtifactResponse[];
  selectedArtifactId: string | undefined;
  selectedEntityType: string | undefined;
  onArtifactChange: (id: string | undefined) => void;
  onEntityTypeChange: (type: string | undefined) => void;
  onReset: () => void;
  hasActiveFilters: boolean;
}

export function GraphFilters({
  artifacts,
  selectedArtifactId,
  selectedEntityType,
  onArtifactChange,
  onEntityTypeChange,
  onReset,
  hasActiveFilters,
}: GraphFiltersProps) {
  const completedArtifacts = artifacts.filter((a) => a.status === "completed");

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-1.5 text-slate-400">
        <Filter className="h-3.5 w-3.5" />
        <span className="text-xs font-medium">Filter</span>
      </div>

      {/* Entity Type Filter */}
      <div className="relative">
        <select
          value={selectedEntityType ?? ""}
          onChange={(e) => onEntityTypeChange(e.target.value || undefined)}
          className="h-8 appearance-none rounded-md border border-slate-700 bg-slate-900 pl-3 pr-8 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer"
        >
          <option value="">All entity types</option>
          {ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t.charAt(0) + t.slice(1).toLowerCase()}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-500" />
      </div>

      {/* Artifact Filter */}
      {completedArtifacts.length > 0 && (
        <div className="relative">
          <select
            value={selectedArtifactId ?? ""}
            onChange={(e) => onArtifactChange(e.target.value || undefined)}
            className="h-8 max-w-[200px] appearance-none rounded-md border border-slate-700 bg-slate-900 pl-3 pr-8 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer"
          >
            <option value="">All documents</option>
            {completedArtifacts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.filename.length > 24 ? `${a.filename.slice(0, 22)}…` : a.filename}
              </option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-slate-500" />
        </div>
      )}

      {hasActiveFilters && (
        <button
          onClick={onReset}
          className="flex items-center gap-1 rounded-md border border-rose-900/40 bg-rose-950/30 px-2.5 py-1 text-xs text-rose-400 transition hover:bg-rose-950/60"
        >
          <X className="h-3 w-3" />
          Clear
        </button>
      )}
    </div>
  );
}

interface EntityTypeLegendProps {
  activeTypes: Set<string>;
  selectedType: string | undefined;
  onSelect: (type: string | undefined) => void;
}

export function EntityTypeLegend({ activeTypes, selectedType, onSelect }: EntityTypeLegendProps) {
  if (activeTypes.size === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5">
      {[...activeTypes].map((type) => {
        const style = getEntityTypeStyle(type);
        const isSelected = selectedType === type;
        return (
          <button
            key={type}
            onClick={() => onSelect(isSelected ? undefined : type)}
            className={clsx(
              "flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium transition-all",
              isSelected
                ? `${style.bg} ${style.border} ${style.text}`
                : "border-slate-800 bg-slate-900/50 text-slate-500 hover:border-slate-700 hover:text-slate-300"
            )}
          >
            <span
              className="h-1.5 w-1.5 rounded-full"
              style={{ backgroundColor: style.node }}
            />
            {type.charAt(0) + type.slice(1).toLowerCase()}
          </button>
        );
      })}
    </div>
  );
}
