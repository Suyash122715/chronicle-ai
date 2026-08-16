export type ExtractionStatus = "SUCCESS" | "PARTIAL" | "FAILED" | "NOT_SUPPORTED" | "SKIPPED";
export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";

export interface ProvenanceItem {
  evidence: string;
  source: string;
  method: string;
  confidence: string;
  metadata: Record<string, unknown>;
}

export interface ExtractionResponse {
  artifact_id: string;
  document_type: string;
  structured_data: Record<string, unknown>;
  provenance: Record<string, ProvenanceItem>;
  warnings: string[];
  confidence: ConfidenceLevel | string;
  status: ExtractionStatus | string;
  extractor_version: string;
  prompt_version: string;
  llm_metadata: Record<string, unknown>;
  started_at: string;
  completed_at: string;
  error_message: string | null;
}
