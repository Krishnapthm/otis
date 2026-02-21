import api from "./authApi";

export interface ReadMCQ {
  mcq_id: string;
  generated_at: string;
  mcq: any;
}

export interface CreateMCQ {
  mcq: any;
}

const mcqApi = {
  // GET /mcqs/ - try common prefixes (/v1/mcqs/ then /mcqs/)
  getAll: async (limit: number = 50, skip: number = 0) => {
    const params = { limit, skip };
    try {
      const res = await api.get<ReadMCQ[]>("/v1/mcqs/", { params });
      return res.data;
    } catch (e) {
      const res = await api.get<ReadMCQ[]>("/mcqs/", { params });
      return res.data;
    }
  },

  // GET /mcqs/{id} - backend may return a list for a project id
  getById: async (id: string) => {
    try {
      const res = await api.get<ReadMCQ[]>(`/v1/mcqs/${id}`);
      return res.data;
    } catch (e) {
      const res = await api.get<ReadMCQ[]>(`/mcqs/${id}`);
      return res.data;
    }
  },

  // Download exported JSON from /mcqs/download/{id}
  download: async (id: string) => {
    try {
      const res = await api.get(`/v1/mcqs/download/${id}`, {
        responseType: "blob",
      });
      return res.data;
    } catch (e) {
      const res = await api.get(`/mcqs/download/${id}`, {
        responseType: "blob",
      });
      return res.data;
    }
  },
};

export default mcqApi;
