/**
 * Knowledge Graph API response types.
 * Mirrors the backend GraphResponse schemas exactly.
 */

export interface GraphProvenanceResponse {
  artifact_id: string;
  extraction_id: string | null;
  confidence: string;
  evidence_snippet: string | null;
  source_location: string | null;
  extraction_method: string;
  metadata: Record<string, unknown>;
}

export interface GraphNodeResponse {
  id: string;
  user_id: string;
  entity_type: string;
  name: string;
  canonical_name: string;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  provenance: GraphProvenanceResponse[];
}

export interface GraphEdgeResponse {
  id: string;
  user_id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  weight: number;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  provenance: GraphProvenanceResponse[];
}

export interface KnowledgeGraphResponse {
  nodes: GraphNodeResponse[];
  edges: GraphEdgeResponse[];
  total_nodes: number;
  total_edges: number;
}

/** Parameters for GET /api/v1/graph */
export interface GraphQueryParams {
  artifact_id?: string;
  entity_type?: string;
  include_provenance?: boolean;
}

/** The set of known entity types (mirrors domain EntityType enum) */
export const ENTITY_TYPES = [
  "SKILL",
  "PROJECT",
  "COMPANY",
  "ROLE",
  "TECHNOLOGY",
  "CERTIFICATE",
  "INSTITUTION",
  "ACHIEVEMENT",
] as const;

export type EntityType = (typeof ENTITY_TYPES)[number];
