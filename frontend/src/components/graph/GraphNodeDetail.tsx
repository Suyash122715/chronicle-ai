"use client";

import React from "react";
import { GraphNodeResponse, GraphEdgeResponse } from "@/types/graph";
import { getEntityTypeStyle } from "./GraphFilters";
import { X, ChevronDown, ChevronUp, Info } from "lucide-react";
import { clsx } from "clsx";

interface GraphNodeDetailProps {
  node: GraphNodeResponse | null;
  edges: GraphEdgeResponse[];
  allNodes: GraphNodeResponse[];
  onClose: () => void;
}

export function GraphNodeDetail({ node, edges, allNodes, onClose }: GraphNodeDetailProps) {
  const [showProvenance, setShowProvenance] = React.useState(false);

  if (!node) return null;

  const style = getEntityTypeStyle(node.entity_type);

  // Find connected edges (as source or target)
  const connectedEdges = edges.filter(
    (e) => e.source_entity_id === node.id || e.target_entity_id === node.id
  );
  const nodeById = Object.fromEntries(allNodes.map((n) => [n.id, n]));

  const properties = Object.entries(node.properties || {}).filter(([, v]) => v != null && v !== "");

  return (
    <aside className="flex h-full w-80 flex-col border-l border-slate-800 bg-slate-950/95 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-800 p-4">
        <div className="flex-1 min-w-0 space-y-1">
          <span
            className={clsx(
              "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
              style.bg,
              style.border,
              style.text
            )}
          >
            <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: style.node }} />
            {node.entity_type}
          </span>
          <h3 className="truncate text-base font-semibold text-white">{node.name}</h3>
          {node.canonical_name !== node.name && (
            <p className="truncate text-[11px] text-slate-500">aka {node.canonical_name}</p>
          )}
        </div>
        <button
          onClick={onClose}
          className="ml-2 rounded-md p-1 text-slate-500 transition hover:bg-slate-800 hover:text-slate-300"
          aria-label="Close detail panel"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-5 p-4">
        {/* Properties */}
        {properties.length > 0 && (
          <section>
            <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
              Properties
            </h4>
            <dl className="space-y-2">
              {properties.map(([k, v]) => (
                <div key={k} className="rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2">
                  <dt className="text-[10px] uppercase tracking-wide text-slate-500">{k.replace(/_/g, " ")}</dt>
                  <dd className="mt-0.5 text-xs text-slate-200 break-words">
                    {typeof v === "object" ? JSON.stringify(v) : String(v)}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        {/* Relationships */}
        {connectedEdges.length > 0 && (
          <section>
            <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
              Relationships ({connectedEdges.length})
            </h4>
            <ul className="space-y-1.5">
              {connectedEdges.map((edge) => {
                const isSource = edge.source_entity_id === node.id;
                const otherId = isSource ? edge.target_entity_id : edge.source_entity_id;
                const other = nodeById[otherId];
                const otherStyle = other ? getEntityTypeStyle(other.entity_type) : getEntityTypeStyle("UNKNOWN");
                return (
                  <li
                    key={edge.id}
                    className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/50 px-3 py-2"
                  >
                    <div className="flex flex-1 min-w-0 items-center gap-1.5">
                      {!isSource && (
                        <span className="shrink-0 text-[10px] text-slate-600">←</span>
                      )}
                      <span
                        className={clsx(
                          "truncate rounded border px-1.5 py-0.5 text-[10px] font-medium",
                          otherStyle.bg,
                          otherStyle.border,
                          otherStyle.text
                        )}
                      >
                        {other?.name ?? otherId.slice(0, 8) + "…"}
                      </span>
                      {isSource && (
                        <span className="shrink-0 text-[10px] text-slate-600">→</span>
                      )}
                    </div>
                    <span className="shrink-0 rounded bg-slate-800 px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-slate-400">
                      {edge.relationship_type.replace(/_/g, " ")}
                    </span>
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {/* Provenance */}
        {node.provenance.length > 0 && (
          <section>
            <button
              onClick={() => setShowProvenance((p) => !p)}
              className="flex w-full items-center justify-between text-[10px] font-semibold uppercase tracking-widest text-slate-500 hover:text-slate-400 transition"
            >
              <span className="flex items-center gap-1">
                <Info className="h-3 w-3" />
                Provenance ({node.provenance.length})
              </span>
              {showProvenance ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>

            {showProvenance && (
              <ul className="mt-2 space-y-2">
                {node.provenance.map((p, i) => (
                  <li
                    key={`${p.artifact_id}-${i}`}
                    className="rounded-lg border border-slate-800 bg-slate-900/50 p-3 space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-slate-400">
                        {p.confidence}
                      </span>
                      <span className="text-[10px] text-slate-600 truncate">{p.extraction_method}</span>
                    </div>
                    {p.evidence_snippet && (
                      <p className="text-[11px] italic text-slate-400 line-clamp-3">
                        &ldquo;{p.evidence_snippet}&rdquo;
                      </p>
                    )}
                    {p.source_location && (
                      <p className="text-[10px] text-slate-600">📍 {p.source_location}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        )}
      </div>

      {/* Footer meta */}
      <div className="border-t border-slate-800 px-4 py-3 text-[10px] text-slate-600">
        ID: {node.id.slice(0, 8)}… · Updated {new Date(node.updated_at).toLocaleDateString()}
      </div>
    </aside>
  );
}

export default GraphNodeDetail;
