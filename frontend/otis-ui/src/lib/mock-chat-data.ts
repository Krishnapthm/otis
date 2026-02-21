import type { ChatConversation, ChatMessage, Citation, ThinkingStep } from "./chat-types";

// ============================================================================
// Mock Thinking Steps
// ============================================================================

const MOCK_THINKING_STEPS: ThinkingStep[] = [
    { label: "Understanding the question", status: "complete" },
    { label: "Searching knowledge base", description: "Found 3 relevant documents", status: "complete" },
    { label: "Analyzing documents", description: "Cross-referencing sources", status: "complete" },
    { label: "Generating response", status: "complete" },
];

// ============================================================================
// Mock Citations
// ============================================================================

const MOCK_CITATIONS: Citation[] = [
    {
        id: "cit-1",
        number: "1",
        title: "Project Requirements Document",
        url: "https://docs.example.com/requirements",
        description: "The main requirements document outlining the project scope and objectives.",
        quote: "The system shall support concurrent users with real-time collaboration features.",
    },
    {
        id: "cit-2",
        number: "2",
        title: "Technical Architecture Overview",
        url: "https://docs.example.com/architecture",
        description: "High-level architecture document describing the system components and their interactions.",
        quote: "Microservices pattern is recommended for independent scaling of subsystems.",
    },
];

// ============================================================================
// Mock Messages
// ============================================================================

const createMockAssistantMessage = (id: string, content: string, withCitations = false): ChatMessage => ({
    id,
    role: "assistant",
    content,
    createdAt: new Date().toISOString(),
    thinking: MOCK_THINKING_STEPS,
    citations: withCitations ? MOCK_CITATIONS : undefined,
});

const MOCK_RESPONSES: string[] = [
    "Based on the documents I've analyzed, the project requirements specify a microservices architecture with the following key components [1]:\n\n1. **API Gateway** — Handles routing, rate limiting, and authentication\n2. **User Service** — Manages user accounts and permissions\n3. **Document Service** — Handles document storage and retrieval\n4. **Notification Service** — Manages real-time notifications via WebSocket\n\nThe architecture document [2] recommends using event-driven communication between services to ensure loose coupling and independent deployability.",

    "I found several relevant sections in your knowledge base. Here's a summary:\n\n**Key Findings:**\n- The system currently supports up to 10,000 concurrent users\n- Average response time is under 200ms for 95th percentile\n- The database layer uses PostgreSQL with read replicas\n\nWould you like me to dive deeper into any of these areas?",

    "Great question! Let me walk through the implementation details.\n\nThe recommended approach involves:\n\n```typescript\nconst handleSubmit = async (data: FormData) => {\n  const response = await api.post('/submit', data);\n  return response.json();\n};\n```\n\nThis pattern ensures proper error handling and type safety throughout the request lifecycle. The API layer abstracts the HTTP details, making it easy to swap implementations later.",
];

let responseIndex = 0;

export function generateMockResponse(_userMessage: string): ChatMessage {
    const content = MOCK_RESPONSES[responseIndex % MOCK_RESPONSES.length];
    const withCitations = responseIndex % MOCK_RESPONSES.length === 0;
    responseIndex++;

    return createMockAssistantMessage(
        `msg-${Date.now()}`,
        content,
        withCitations,
    );
}

// ============================================================================
// Mock Conversation History
// ============================================================================

export const MOCK_CONVERSATIONS: ChatConversation[] = [
    {
        id: "conv-1",
        title: "Project Architecture Review",
        updatedAt: "2026-02-20T12:00:00Z",
        messages: [
            { id: "m1", role: "user", content: "Can you review the project architecture?", createdAt: "2026-02-20T11:55:00Z" },
            createMockAssistantMessage("m2", MOCK_RESPONSES[0], true),
        ],
    },
    {
        id: "conv-2",
        title: "Performance Analysis",
        updatedAt: "2026-02-19T16:30:00Z",
        messages: [
            { id: "m3", role: "user", content: "What are the current performance metrics?", createdAt: "2026-02-19T16:25:00Z" },
            createMockAssistantMessage("m4", MOCK_RESPONSES[1]),
        ],
    },
    {
        id: "conv-3",
        title: "API Integration Help",
        updatedAt: "2026-02-18T09:15:00Z",
        messages: [
            { id: "m5", role: "user", content: "How should I implement the form submission?", createdAt: "2026-02-18T09:10:00Z" },
            createMockAssistantMessage("m6", MOCK_RESPONSES[2]),
        ],
    },
    {
        id: "conv-4",
        title: "Database Schema Design",
        updatedAt: "2026-02-17T14:00:00Z",
        messages: [],
    },
    {
        id: "conv-5",
        title: "Security Audit Checklist",
        updatedAt: "2026-02-16T10:00:00Z",
        messages: [],
    },
];

export function getMockConversation(chatId: string): ChatConversation | undefined {
    return MOCK_CONVERSATIONS.find((c) => c.id === chatId);
}

export function generateChatTitle(message: string): string {
    return message.length > 40 ? `${message.slice(0, 40)}...` : message;
}
