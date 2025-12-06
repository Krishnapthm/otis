import api from "./authApi";

// Matches your Pydantic "ProjectBase"
export interface ProjectInput {
  project_name: string;
  project_desc?: string;
}

// Matches your Pydantic "ProjectResponse"
export interface ProjectResponse {
  project_id: string;
  project_name: string;
  project_desc: string; // Backend might return null, but we'll handle it
  created_at: string;
  created_by: string; // This is a UUID from the backend
}

export const projectApi = {
  // GET /projects/?limit=50&skip=0
  getAll: async (limit: number = 50, skip: number = 0) => {
    const res = await api.get<ProjectResponse[]>("/v1/projects/", {
      params: { limit, skip },
    });
    return res.data;
  },

  // GET /projects/{project_id}
  getOne: async (projectId: string) => {
    const res = await api.get<ProjectResponse>(`/v1/projects/${projectId}`);
    return res.data;
  },

  // POST /projects/
  create: async (data: ProjectInput) => {
    const res = await api.post<ProjectResponse>("/v1/projects/", data);
    return res.data;
  },

  // DELETE /projects/{project_id}
  delete: async (projectId: string) => {
    const res = await api.delete<{ message: string }>(
      `/v1/projects/${projectId}`
    );
    return res.data;
  },
};
