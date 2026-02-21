// Agent API client for graph SSE endpoints

// ============================================================================
// Types
// ============================================================================

export interface Concept {
  name: string;
  summary: string;
}

export interface Overview {
  doc_name: string;
  concepts: Concept[];
}

export type AgentEventType =
  | "status"
  | "concepts_extracted"
  | "interrupt"
  | "queries_generated"
  | "retrieval_complete"
  | "error";

export interface AgentEvent {
  mode: string;
  payload: {
    status?: string;
    overview?: Overview[];
    overview_for_user?: Overview[];
    num_docs?: number;
    num_queries?: number;
    docs?: number;
    error?: string;
  };
}

export interface StartGraphRequest {
  doc_ids: string[];
}

export interface ResumeRequest {
  selected_concepts: Concept[];
}

// ============================================================================
// API Functions
// ============================================================================

const API_BASE = "http://localhost:8000";

/**
 * Get the auth token for SSE requests
 */
function getAuthToken(): string | null {
  return localStorage.getItem("access_token");
}

/**
 * Start the graph SSE stream
 * Returns an EventSource and the thread_id from response headers
 */
export async function startGraphStream(
  docIds: string[],
  onEvent: (event: AgentEvent) => void,
  onError: (error: string) => void,
  onComplete: () => void,
): Promise<{ close: () => void; threadIdPromise: Promise<string> }> {
  const token = getAuthToken();

  // Use fetch with streaming for SSE since we need to access headers
  // and send POST request with body
  const response = await fetch(`${API_BASE}/v1/graph/start`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ doc_ids: docIds }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }

  const threadId = response.headers.get("X-Thread-ID") || "";

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let isAborted = false;

  const processStream = async () => {
    if (!reader) {
      onError("No response body");
      return;
    }

    try {
      while (!isAborted) {
        const { done, value } = await reader.read();

        if (done) {
          onComplete();
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Process SSE events from buffer
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              onEvent(data as AgentEvent);
            } catch (e) {
              console.error("Failed to parse SSE event:", e);
            }
          }
        }
      }
    } catch (error) {
      if (!isAborted) {
        onError(error instanceof Error ? error.message : "Stream error");
      }
    }
  };

  // Start processing in background
  processStream();

  return {
    close: () => {
      isAborted = true;
      reader?.cancel();
    },
    threadIdPromise: Promise.resolve(threadId),
  };
}

/**
 * Resume the graph with selected concepts
 */
export async function resumeGraphStream(
  threadId: string,
  selectedConcepts: Concept[],
  onEvent: (event: AgentEvent) => void,
  onError: (error: string) => void,
  onComplete: () => void,
): Promise<{ close: () => void }> {
  const token = getAuthToken();

  const response = await fetch(`${API_BASE}/v1/graph/resume/${threadId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ selected_concepts: selectedConcepts }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let isAborted = false;

  const processStream = async () => {
    if (!reader) {
      onError("No response body");
      return;
    }

    try {
      while (!isAborted) {
        const { done, value } = await reader.read();

        if (done) {
          onComplete();
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              onEvent(data as AgentEvent);
            } catch (e) {
              console.error("Failed to parse SSE event:", e);
            }
          }
        }
      }
    } catch (error) {
      if (!isAborted) {
        onError(error instanceof Error ? error.message : "Stream error");
      }
    }
  };

  processStream();

  return {
    close: () => {
      isAborted = true;
      reader?.cancel();
    },
  };
}

export default {
  startGraphStream,
  resumeGraphStream,
};
