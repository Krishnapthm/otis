import api from "./authApi";

export interface Document {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  file_path: string;
  project_id: string;
  user_id: string;
  is_embedded: boolean;
  embedded_at: string | null;
  created_at: string;
  updated_at: string | null;
}

export async function uploadDocuments(
  projectId: string,
  files: File[],
): Promise<Document[]> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const res = await api.post(`/v1/project/${projectId}/documents/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return res.data;
}

export async function getAllDocuments(projectId: string): Promise<Document[]> {
  const res = await api.get(`/v1/project/${projectId}/documents/`);
  return res.data;
}

export async function getDocument(
  projectId: string,
  docId: string,
): Promise<Document> {
  const res = await api.get(`/v1/project/${projectId}/documents/${docId}`);
  return res.data;
}

export async function deleteDocuments(
  projectId: string,
  docIds: string[],
): Promise<void> {
  const res = await api.delete(`/v1/project/${projectId}/documents/`, {
    data: { doc_id: docIds },
  });
  return res.data;
}

export async function downloadDocuments(projectId: string): Promise<Blob> {
  const res = await api.get(`/v1/project/${projectId}/documents/download`, {
    responseType: "blob",
  });
  return res.data;
}

// Fix for delete function - need projectId in scope
export async function deleteDocumentsFromProject(
  projectId: string,
  docIds: string[],
): Promise<void> {
  const res = await api.delete(`/v1/project/${projectId}/documents/`, {
    data: { doc_id: docIds },
  });
  return res.data;
}

// ===== USER-LEVEL DOCUMENT OPERATIONS =====

// Get all documents owned by the user (user-level)
export async function getAllUserDocuments(): Promise<Document[]> {
  const res = await api.get("/v1/documents/");
  return res.data;
}

// Get a specific document by ID (user-level)
export async function getUserDocument(docId: string): Promise<Document> {
  const res = await api.get(`/v1/documents/${docId}`);
  return res.data;
}

// Link an existing user document to a project
export async function linkDocumentToProject(
  projectId: string,
  docId: string,
): Promise<{ message: string }> {
  const res = await api.post(`/v1/project/${projectId}/documents/link`, {
    doc_ids: [docId], // Backend expects array of doc_ids
  });
  return res.data;
}

// Download a document by ID (user-level)
export async function downloadDocument(docId: string): Promise<Blob> {
  const res = await api.get(`/v1/documents/${docId}/download`, {
    responseType: "blob",
  });
  return res.data;
}

// Get document thumbnail URL (user-level)
export function getThumbnailUrl(docId: string): string {
  return `${api.defaults.baseURL}/v1/documents/${docId}/thumbnail`;
}

// Upload documents at user level (not tied to a project)
export async function uploadUserDocuments(files: File[]): Promise<Document[]> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const res = await api.post("/v1/documents/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return res.data;
}
