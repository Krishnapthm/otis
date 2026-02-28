import api from "./authApi";

export interface ReadMCQ {
  mcq_id: string;
  mcq: MCQTest;
}

export interface CreateMCQ {
  mcq: MCQTest;
}

export interface MCQOption {
  key: "A" | "B" | "C" | "D";
  text: string;
}

export interface MCQQuestion {
  question_index: number;
  question: string;
  options: MCQOption[];
  right_answer: "A" | "B" | "C" | "D";
  explanation: string;
}

export interface MCQTest {
  test_id: string;
  doc_ids: string[];
  plan: Record<string, unknown>;
  questions: MCQQuestion[];
  test_name: string;
  created_at: string;
}

export type MCQExportMode = "raw" | "test";
export type MCQExportFormat = "md" | "json" | "pdf" | "docx";

const mcqApi = {
  // GET /mcqs/ - try common prefixes (/v1/mcqs/ then /mcqs/)
  getAll: async (limit: number = 50, skip: number = 0) => {
    const params = { limit, skip };
    try {
      const res = await api.get<ReadMCQ[]>("/v1/mcqs/", { params });
      return res.data;
    } catch {
      const res = await api.get<ReadMCQ[]>("/mcqs/", { params });
      return res.data;
    }
  },

  // GET /mcqs/{id} - backend may return a list for a project id
  getById: async (id: string) => {
    try {
      const res = await api.get<ReadMCQ[]>(`/v1/mcqs/${id}`);
      return res.data;
    } catch {
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
    } catch {
      const res = await api.get(`/mcqs/download/${id}`, {
        responseType: "blob",
      });
      return res.data;
    }
  },

  exportMcq: async (
    id: string,
    mode: MCQExportMode,
    format: MCQExportFormat,
  ) => {
    const params = { mode, format };
    try {
      const res = await api.get(`/v1/mcqs/${id}/export`, {
        params,
        responseType: "blob",
      });
      return res;
    } catch {
      const res = await api.get(`/mcqs/${id}/export`, {
        params,
        responseType: "blob",
      });
      return res;
    }
  },
};

export default mcqApi;
