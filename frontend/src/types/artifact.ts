export type ProcessingStatus = "pending" | "processing" | "completed" | "failed";

export interface ArtifactResponse {
  id: string;
  user_id: string;
  filename: string;
  stored_filename: string;
  file_size: number;
  mime_type: string;
  status: ProcessingStatus;
  raw_text: string | null;
  document_type: string | null;
  classification_confidence: string | null;
  classifier_version: string | null;
  classified_at: string | null;
  error_message: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export interface UploadArtifactResponse {
  artifact: ArtifactResponse;
  message: string;
}
