"use client";

import React, { useState, useMemo } from "react";
import { useKnowledgeGraph } from "@/hooks/useKnowledgeGraph";
import { useArtifacts } from "@/hooks/useArtifacts";
import { GraphVisualization } from "@/components/graph/GraphVisualization";
import { GraphNodeDetail } from "@/components/graph/GraphNodeDetail";
import { GraphFilters, EntityTypeLegend } from "@/components/graph/GraphFilters";
import { GraphEmptyState } from "@/components/graph/GraphEmptyState";
import { GraphLoadingSkeleton } from "@/components/graph/GraphLoadingSkeleton";
import { GraphStatsBar } from "@/components/graph/GraphStatsBar";
import { Alert } from "@/components/ui/Alert";
import { GraphNodeResponse } from "@/types/graph";
import { RefreshCw } from "lucide-react";

export default function GraphPage() {
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | undefined>();
  const [selectedEntityType, setSelectedEntityType] = useState<string | undefined>();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const hasActiveFilters = Boolean(selectedArtifactId || selectedEntityType);

  const { data: graph, isLoading, isError, error, refetch, isFetching } = useKnowledgeGraph({
    artifact_id: selectedArtifactId,
    entity_type: selectedEntityType,
    include_provenance: true,
  });

  const { data: artifacts = [] } = useArtifacts();

  const activeEntityTypes = useMemo(() => {
    const types = new Set<string>();
    (graph?.nodes ?? []).forEach((n) => types.add(n.entity_type));
    return types;
  }, [graph?.nodes]);

  const selectedNode: GraphNodeResponse | null = useMemo(() => {
    if (!selectedNodeId || !graph) return null;
    return graph.nodes.find((n) => n.id === selectedNodeId) ?? null;
  }, [selectedNodeId, graph]);

  const handleReset = () => {
    setSelectedArtifactId(undefined);
    setSelectedEntityType(undefined);
    setSelectedNodeId(null);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col gap-4 overflow-hidden">
      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-3 border-b border-slate-800 pb-4 shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-white">Knowledge Graph</h2>
            <p className="text-sm text-slate-400">
              Visual map of entities and relationships extracted from your documents.
            </p>
          </div>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white disabled:opacity-50"
            aria-label="Refresh graph"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Filters row */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <GraphFilters
            artifacts={artifacts}
            selectedArtifactId={selectedArtifactId}
            selectedEntityType={selectedEntityType}
            onArtifactChange={(id) => {
              setSelectedArtifactId(id);
              setSelectedNodeId(null);
            }}
            onEntityTypeChange={(type) => {
              setSelectedEntityType(type);
              setSelectedNodeId(null);
            }}
            onReset={handleReset}
            hasActiveFilters={hasActiveFilters}
          />

          {graph && (
            <GraphStatsBar
              totalNodes={graph.total_nodes}
              totalEdges={graph.total_edges}
              activeEntityTypes={activeEntityTypes.size}
            />
          )}
        </div>

        {/* Entity type legend (clickable quick-filter) */}
        {activeEntityTypes.size > 0 && (
          <EntityTypeLegend
            activeTypes={activeEntityTypes}
            selectedType={selectedEntityType}
            onSelect={(type) => {
              setSelectedEntityType(type);
              setSelectedNodeId(null);
            }}
          />
        )}
      </div>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <div className="flex min-h-0 flex-1 gap-0 overflow-hidden rounded-xl border border-slate-800">
        {/* Canvas */}
        <div className="relative flex-1 min-w-0 bg-slate-950">
          {isLoading ? (
            <GraphLoadingSkeleton />
          ) : isError ? (
            <div className="flex h-full items-center justify-center p-8">
              <Alert variant="error" message={error?.message ?? "Failed to load knowledge graph."} />
            </div>
          ) : !graph || graph.nodes.length === 0 ? (
            <GraphEmptyState hasFilters={hasActiveFilters} onReset={handleReset} />
          ) : (
            <GraphVisualization
              graphNodes={graph.nodes}
              graphEdges={graph.edges}
              selectedNodeId={selectedNodeId}
              onNodeSelect={setSelectedNodeId}
            />
          )}

          {/* Fetching overlay */}
          {isFetching && !isLoading && (
            <div className="absolute top-3 right-3 flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-900/90 px-3 py-1.5 text-[11px] text-slate-400 backdrop-blur-sm">
              <RefreshCw className="h-3 w-3 animate-spin text-emerald-400" />
              Updating…
            </div>
          )}
        </div>

        {/* Node detail panel */}
        {selectedNode && (
          <GraphNodeDetail
            node={selectedNode}
            edges={graph?.edges ?? []}
            allNodes={graph?.nodes ?? []}
            onClose={() => setSelectedNodeId(null)}
          />
        )}
      </div>
    </div>
  );
}
