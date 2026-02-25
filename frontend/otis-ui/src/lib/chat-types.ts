// ============================================================================
// Shared Chat Types
// ============================================================================

export interface Citation {
  id: string;
  number: string;
  title: string;
  url: string;
  description: string;
  quote?: string;
}

export interface ThinkingStep {
  label: string;
  description?: string;
  status: "complete" | "active" | "pending";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  isStreaming?: boolean;
  thinking?: ThinkingStep[];
  citations?: Citation[];
}

export interface ChatConversation {
  id: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
}
