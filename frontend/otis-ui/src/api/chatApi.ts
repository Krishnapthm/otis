import api from "./authApi";

// ============================================================================
// Types — mirrors the Pydantic schemas exactly
// ============================================================================

export interface ChatResponse {
  chat_id: string;
  user_id: string;
  status: "active" | "archived" | "deleted";
  total_input_tokens: number;
  total_output_tokens: number;
  title: string | null;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
  deleted_at: string | null;
}

export interface ChatCreate {
  title?: string | null;
}

export interface ChatUpdate {
  title?: string | null;
  status?: "active" | "archived" | "deleted" | null;
}

export type MessageRole = "user" | "assistant" | "tool";
export type MessageStatus = "pending" | "streaming" | "completed" | "failed";

export interface ChatMessageResponse {
  message_id: string;
  chat_id: string;
  role: MessageRole;
  sequence: number;
  status: MessageStatus;
  content: string | null;
  structured_data: Record<string, unknown> | null;
  doc_ids: string[];
  input_tokens: number | null;
  output_tokens: number | null;
  error: Record<string, unknown> | null;
  created_at: string;
}

export interface ChatMessageCreate {
  role: MessageRole;
  content?: string | null;
  structured_data?: Record<string, unknown> | null;
  doc_ids?: string[] | null;
  status?: MessageStatus;
  input_tokens?: number | null;
  output_tokens?: number | null;
  error?: Record<string, unknown> | null;
}

export interface ChatMessageUpdate {
  content?: string | null;
  structured_data?: Record<string, unknown> | null;
  doc_ids?: string[] | null;
  status?: MessageStatus | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
  error?: Record<string, unknown> | null;
}

export interface ChatInvokeStartedEvent {
  event: "started";
  user_message: ChatMessageResponse;
  assistant_message_id: string;
}

export interface ChatInvokeTokenEvent {
  event: "token";
  content: string;
}

export interface ChatInvokeDoneEvent {
  event: "done";
  assistant_message: ChatMessageResponse;
}

export interface ChatInvokeErrorEvent {
  event: "error";
  detail: string;
}

export interface ChatInvokeThinkingEvent {
  event: "thinking";
  node: string;
  status: "started" | "completed";
  label: string;
  detail?: string;
}

export interface ChatInvokeReasoningTokenEvent {
  event: "reasoning_token";
  content: string;
  node?: string;
}

export type ChatInvokeEvent =
  | ChatInvokeStartedEvent
  | ChatInvokeTokenEvent
  | ChatInvokeDoneEvent
  | ChatInvokeErrorEvent
  | ChatInvokeThinkingEvent
  | ChatInvokeReasoningTokenEvent;

// ============================================================================
// Chat API
// ============================================================================

export const chatApi = {
  /** POST /v1/chats/ */
  create: async (data: ChatCreate = {}): Promise<ChatResponse> => {
    const res = await api.post<ChatResponse>("/v1/chats/", data);
    return res.data;
  },

  /** GET /v1/chats/ */
  list: async (params?: {
    limit?: number;
    skip?: number;
    status?: string;
  }): Promise<ChatResponse[]> => {
    const res = await api.get<ChatResponse[]>("/v1/chats/", { params });
    return res.data;
  },

  /** GET /v1/chats/{chat_id} */
  get: async (chatId: string): Promise<ChatResponse> => {
    const res = await api.get<ChatResponse>(`/v1/chats/${chatId}`);
    return res.data;
  },

  /** PATCH /v1/chats/{chat_id} */
  update: async (chatId: string, data: ChatUpdate): Promise<ChatResponse> => {
    const res = await api.patch<ChatResponse>(`/v1/chats/${chatId}`, data);
    return res.data;
  },

  /** DELETE /v1/chats/{chat_id} */
  delete: async (chatId: string): Promise<{ message: string }> => {
    const res = await api.delete<{ message: string }>(`/v1/chats/${chatId}`);
    return res.data;
  },

  messages: {
    /** POST /v1/chats/{chat_id}/messages */
    create: async (
      chatId: string,
      data: ChatMessageCreate,
    ): Promise<ChatMessageResponse> => {
      const res = await api.post<ChatMessageResponse>(
        `/v1/chats/${chatId}/messages`,
        data,
      );
      return res.data;
    },

    /** GET /v1/chats/{chat_id}/messages */
    list: async (
      chatId: string,
      params?: { limit?: number; skip?: number },
    ): Promise<ChatMessageResponse[]> => {
      const res = await api.get<ChatMessageResponse[]>(
        `/v1/chats/${chatId}/messages`,
        { params },
      );
      return res.data;
    },

    /** GET /v1/chats/{chat_id}/messages/{message_id} */
    get: async (
      chatId: string,
      messageId: string,
    ): Promise<ChatMessageResponse> => {
      const res = await api.get<ChatMessageResponse>(
        `/v1/chats/${chatId}/messages/${messageId}`,
      );
      return res.data;
    },

    /** PATCH /v1/chats/{chat_id}/messages/{message_id} */
    update: async (
      chatId: string,
      messageId: string,
      data: ChatMessageUpdate,
    ): Promise<ChatMessageResponse> => {
      const res = await api.patch<ChatMessageResponse>(
        `/v1/chats/${chatId}/messages/${messageId}`,
        data,
      );
      return res.data;
    },

    /** DELETE /v1/chats/{chat_id}/messages/{message_id} */
    delete: async (
      chatId: string,
      messageId: string,
    ): Promise<{ message: string }> => {
      const res = await api.delete<{ message: string }>(
        `/v1/chats/${chatId}/messages/${messageId}`,
      );
      return res.data;
    },

    /** POST /v1/chats/{chat_id}/invoke (SSE stream) */
    stream: async (
      chatId: string,
      message: string,
      handlers: {
        onStarted?: (event: ChatInvokeStartedEvent) => void;
        onToken: (chunk: string) => void;
        onDone: (message: ChatMessageResponse) => void;
        onError: (error: string) => void;
        onThinking?: (event: ChatInvokeThinkingEvent) => void;
        onReasoningToken?: (event: ChatInvokeReasoningTokenEvent) => void;
      },
      docIds?: string[],
      mentions?: { id: string; label: string; triggerChar: string }[],
    ): Promise<{ close: () => void }> => {
      const token = localStorage.getItem("access_token");
      const baseURL = (api.defaults.baseURL ?? "").replace(/\/$/, "");

      const response = await fetch(`${baseURL}/v1/chats/${chatId}/invoke`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message, doc_ids: docIds, mentions }),
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
          handlers.onError("No response body");
          return;
        }

        try {
          while (!isAborted) {
            const { done, value } = await reader.read();

            if (done) {
              break;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;

              try {
                const event = JSON.parse(line.slice(6)) as ChatInvokeEvent;

                if (event.event === "started") {
                  handlers.onStarted?.(event);
                } else if (event.event === "token") {
                  handlers.onToken(event.content ?? "");
                } else if (event.event === "done") {
                  handlers.onDone(event.assistant_message);
                } else if (event.event === "error") {
                  handlers.onError(event.detail || "Stream error");
                } else if (event.event === "thinking") {
                  handlers.onThinking?.(event);
                } else if (event.event === "reasoning_token") {
                  handlers.onReasoningToken?.(event);
                }
              } catch (error) {
                console.error("Failed to parse chat stream event:", error);
              }
            }
          }
        } catch (error) {
          if (!isAborted) {
            handlers.onError(
              error instanceof Error ? error.message : "Stream error",
            );
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
    },
  },
};
