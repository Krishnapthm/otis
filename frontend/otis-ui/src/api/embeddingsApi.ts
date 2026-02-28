import api from "./authApi";

// Types
export interface VectorstoreStatus {
  total_documents: number;
  embedded_documents: number;
  pending_documents: number;
  collection_id: string | null;
  status: "ready" | "syncing" | "error";
}

export interface SyncResponse {
  message: string;
  job_id?: string;
  status: string;
}

export interface EmbeddingVersion {
  version_id: string;
  version_name: string;
  project_id: string;
  collection_id: string;
  version_number: number;
  is_active: boolean;
  desc: string | null;
  doc_count: number;
  created_at: string;
}

// Sync all pending documents for the user
export async function syncEmbeddings(): Promise<SyncResponse> {
  const res = await api.post("/v1/embeddings/sync");
  return res.data;
}

// Get vectorstore status
export async function getEmbeddingStatus(): Promise<VectorstoreStatus> {
  const res = await api.get("/v1/embeddings/status");
  return res.data;
}

// Clear vectorstore (optional - for advanced settings)
export async function clearVectorstore(): Promise<{ message: string }> {
  const res = await api.delete("/v1/embeddings/clear");
  return res.data;
}
