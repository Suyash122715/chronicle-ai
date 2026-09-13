"use client";

import React, { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Edge,
  Connection,
  BackgroundVariant,
  MarkerType,
  NodeTypes,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { GraphNodeResponse, GraphEdgeResponse } from "@/types/graph";
import { getEntityTypeStyle } from "./GraphFilters";
import { clsx } from "clsx";

// ---------------------------------------------------------------------------
// Custom node component
// ---------------------------------------------------------------------------

interface EntityNodeData {
  label: string;
  entityType: string;
  provenanceCount: number;
  [key: string]: unknown;
}

function EntityNode({ data, selected }: { data: EntityNodeData; selected?: boolean }) {
  const style = getEntityTypeStyle(data.entityType as string);
  const label = data.label as string;
  const entityType = data.entityType as string;
  const provenanceCount = data.provenanceCount as number;

  return (
    <div
      className={clsx(
        "relative flex flex-col items-center justify-center rounded-2xl border-2 px-3 py-2 text-center shadow-lg transition-all duration-200 cursor-pointer min-w-[80px] max-w-[140px]",
        selected
          ? `${style.border} shadow-[0_0_20px_rgba(0,0,0,0.5)]`
          : "border-slate-700/60 hover:border-slate-600",
        "bg-slate-900"
      )}
      style={{
        boxShadow: selected
          ? `0 0 0 2px ${style.node}60, 0 8px 32px rgba(0,0,0,0.5)`
          : undefined,
      }}
    >
      {/* Type badge dot */}
      <span
        className="absolute -top-1.5 -right-1.5 h-3.5 w-3.5 rounded-full border-2 border-slate-900"
        style={{ backgroundColor: style.node }}
      />

      {/* Provenance count */}
      {provenanceCount > 0 && (
        <span className="absolute -top-1.5 -left-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-[8px] font-bold text-slate-400">
          {provenanceCount}
        </span>
      )}

      {/* Entity type label */}
      <span className={clsx("text-[8px] font-semibold uppercase tracking-widest mb-1", style.text)}>
        {entityType.slice(0, 4)}
      </span>

      {/* Name */}
      <span className="text-[11px] font-semibold leading-tight text-white line-clamp-2">
        {label}
      </span>

      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes: NodeTypes = { entity: EntityNode };

// ---------------------------------------------------------------------------
// Layout: simple force-like circular / grid positioning
// ---------------------------------------------------------------------------

function computeLayout(nodes: GraphNodeResponse[]): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  if (nodes.length === 0) return positions;

  // Group by entity type for visual clustering
  const groups: Record<string, GraphNodeResponse[]> = {};
  for (const n of nodes) {
    const t = n.entity_type;
    groups[t] = groups[t] ?? [];
    groups[t].push(n);
  }

  const groupKeys = Object.keys(groups);
  const groupCount = groupKeys.length;
  const radius = Math.max(250, groupCount * 120);

  groupKeys.forEach((type, gi) => {
    const groupAngle = (gi / groupCount) * 2 * Math.PI;
    const gx = radius * Math.cos(groupAngle);
    const gy = radius * Math.sin(groupAngle);

    const members = groups[type];
    const spread = Math.min(120, members.length * 20);

    members.forEach((node, mi) => {
      const subAngle = members.length > 1 ? (mi / members.length) * 2 * Math.PI : 0;
      const subR = members.length > 1 ? spread : 0;
      positions.set(node.id, {
        x: gx + subR * Math.cos(subAngle),
        y: gy + subR * Math.sin(subAngle),
      });
    });
  });

  return positions;
}

// ---------------------------------------------------------------------------
// Transform domain objects → React Flow nodes/edges
// ---------------------------------------------------------------------------

function toFlowNodes(
  graphNodes: GraphNodeResponse[],
  selectedId: string | null
): Node[] {
  const layout = computeLayout(graphNodes);

  return graphNodes.map((n) => {
    const pos = layout.get(n.id) ?? { x: 0, y: 0 };
    return {
      id: n.id,
      type: "entity",
      position: pos,
      data: {
        label: n.name,
        entityType: n.entity_type,
        provenanceCount: n.provenance.length,
      } satisfies EntityNodeData,
      selected: n.id === selectedId,
    };
  });
}

function toFlowEdges(graphEdges: GraphEdgeResponse[]): Edge[] {
  return graphEdges.map((e) => ({
    id: e.id,
    source: e.source_entity_id,
    target: e.target_entity_id,
    label: e.relationship_type.replace(/_/g, " "),
    type: "smoothstep",
    animated: false,
    markerEnd: { type: MarkerType.ArrowClosed, color: "#475569" },
    style: { stroke: "#475569", strokeWidth: 1.5 },
    labelStyle: {
      fill: "#94a3b8",
      fontSize: 9,
      fontWeight: 500,
    },
    labelBgStyle: {
      fill: "#0f172a",
      fillOpacity: 0.8,
    },
    labelBgPadding: [4, 2] as [number, number],
  }));
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

interface GraphVisualizationProps {
  graphNodes: GraphNodeResponse[];
  graphEdges: GraphEdgeResponse[];
  selectedNodeId: string | null;
  onNodeSelect: (id: string | null) => void;
}

export function GraphVisualization({
  graphNodes,
  graphEdges,
  selectedNodeId,
  onNodeSelect,
}: GraphVisualizationProps) {
  const initialNodes = useMemo(
    () => toFlowNodes(graphNodes, selectedNodeId),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [graphNodes]
  );
  const initialEdges = useMemo(() => toFlowEdges(graphEdges), [graphEdges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync when data changes
  React.useEffect(() => {
    setNodes(toFlowNodes(graphNodes, selectedNodeId));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphNodes, selectedNodeId]);

  React.useEffect(() => {
    setEdges(toFlowEdges(graphEdges));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [graphEdges]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      onNodeSelect(node.id === selectedNodeId ? null : node.id);
    },
    [onNodeSelect, selectedNodeId]
  );

  const onPaneClick = useCallback(() => {
    onNodeSelect(null);
  }, [onNodeSelect]);

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3, maxZoom: 1.4 }}
        minZoom={0.2}
        maxZoom={3}
        proOptions={{ hideAttribution: true }}
        style={{ background: "transparent" }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={24}
          size={1}
          color="#1e293b"
        />
        <Controls
          className="!border-slate-800 !bg-slate-900 !shadow-xl"
          showInteractive={false}
        />
        <MiniMap
          className="!border-slate-800 !bg-slate-900/80"
          nodeColor={(node) => {
            const entityType = (node.data?.entityType as string) ?? "";
            const style = getEntityTypeStyle(entityType);
            return style.node;
          }}
          maskColor="rgba(2, 6, 23, 0.7)"
        />
      </ReactFlow>
    </div>
  );
}

export default GraphVisualization;
