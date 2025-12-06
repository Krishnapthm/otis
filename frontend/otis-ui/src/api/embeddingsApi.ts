import api from "./authApi";

// Types
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

export interface CreateEmbeddingRequest {
  version_name: string;
  project_id: string;
  doc_id: string[];
}

export interface DeleteEmbeddingRequest {
  version_ids: string[];
}
// Create embeddings for selected documents
export async function createEmbedding(
  projectId: string,
  data: CreateEmbeddingRequest
): Promise<EmbeddingVersion> {
  const res = await api.post(`/v1/project/${projectId}/embeddings/`, {
    version_name: data.version_name,
    doc_id: data.doc_id,
  });
  return res.data;
}

// List all embeddings for a project
export async function listEmbeddings(
  projectId: string
): Promise<EmbeddingVersion[]> {
  const res = await api.get(`/v1/project/${projectId}/embeddings/`);
  return res.data;
}

// Get a specific embedding by collection_id
export async function getEmbedding(
  projectId: string,
  collectionId: string
): Promise<any> {
  const res = await api.get(
    `/v1/project/${projectId}/embeddings/${collectionId}`
  );
  return res.data;
}

// Update an embedding
export async function updateEmbedding(
  projectId: string,
  collectionId: string,
  data: Partial<EmbeddingVersion>
): Promise<any> {
  const res = await api.put(
    `/v1/project/${projectId}/embeddings/${collectionId}`,
    data
  );
  return res.data;
}

// Delete embedding versions
export async function deleteEmbeddings(
  projectId: string,
  versionIds: string[]
): Promise<{ deleted_count: number }> {
  const res = await api.delete(`/v1/project/${projectId}/embeddings/`, {
    data: { version_ids: versionIds },
  });
  return res.data;
}

// Batch delete helper
export async function batchDeleteEmbeddings(
  projectId: string,
  versionIds: string[]
): Promise<{ deleted_count: number }> {
  return deleteEmbeddings(projectId, versionIds);
}
