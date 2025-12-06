import api from "./authApi";

export interface Document {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  file_path: string;
  project_id: string;
  created_at: string;
  updated_at: string | null;
}

export async function uploadDocuments(
  projectId: string,
  files: File[]
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
  docId: string
): Promise<Document> {
  const res = await api.get(`/v1/project/${projectId}/documents/${docId}`);
  return res.data;
}

export async function deleteDocuments(
  projectId: string,
  docIds: string[]
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
  docIds: string[]
): Promise<void> {
  const res = await api.delete(`/v1/project/${projectId}/documents/`, {
    data: { doc_id: docIds },
  });
  return res.data;
}
