// ============================================================================
// Centralized Query Key Factory
// ============================================================================

export const queryKeys = {
    documents: {
        all: ["documents"] as const,
        detail: (docId: string) => ["documents", docId] as const,
    },
    chat: {
        all: ["chat"] as const,
        detail: (chatId: string) => ["chat", chatId] as const,
        messages: (chatId: string) => ["chat", chatId, "messages"] as const,
        attachments: (chatId: string) => ["chat", chatId, "attachments"] as const,
    },
};
