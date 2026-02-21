// ============================================================================
// Mention Picker — Types
// ============================================================================

// ---------------------------------------------------------------------------
// Token Model
// ---------------------------------------------------------------------------

export interface TextToken {
    type: "text";
    value: string;
}

export interface MentionToken {
    type: "mention";
    /** Stable ID from the data source (e.g. "doc_001") */
    id: string;
    /** Display label (e.g. "API_Documentation.pdf") */
    label: string;
    /** The trigger char that opened this mention (e.g. "@") */
    triggerChar: string;
}

export type Token = TextToken | MentionToken;

// ---------------------------------------------------------------------------
// Mention Item (data source row)
// ---------------------------------------------------------------------------

export interface MentionItem {
    id: string;
    label: string;
}

// ---------------------------------------------------------------------------
// Trigger Configuration
// ---------------------------------------------------------------------------

export interface TriggerConfig {
    /** The character that activates this trigger (e.g. "@") */
    char: string;
    /** Logical type identifier (e.g. "document", "tag", "emoji") */
    type: string;
    /** Static item list — replace with fetchItems for async */
    items?: MentionItem[];
    /** Future: async item loader */
    fetchItems?: (query: string) => Promise<MentionItem[]>;
}

// ---------------------------------------------------------------------------
// Active Trigger Session
// ---------------------------------------------------------------------------

export interface ActiveTrigger {
    config: TriggerConfig;
    /** Index in the raw textarea value where the trigger char sits */
    triggerStart: number;
    /** Query text typed after the trigger char */
    query: string;
}

// ---------------------------------------------------------------------------
// Caret coordinates (pixel, relative to viewport)
// ---------------------------------------------------------------------------

export interface CaretCoords {
    x: number;
    y: number;
    /** Height of a single line, for dropdown vertical offset */
    lineHeight: number;
}

// ---------------------------------------------------------------------------
// API Payload
// ---------------------------------------------------------------------------

export interface MentionPayload {
    /** Plain text string with no mention syntax */
    plainText: string;
    /** Resolved mention objects for the backend */
    mentions: { id: string; label: string; triggerChar: string }[];
}

// ---------------------------------------------------------------------------
// Async status
// ---------------------------------------------------------------------------

export type MentionStatus = "idle" | "loading" | "success" | "error";

// ---------------------------------------------------------------------------
// Mock Data
// ---------------------------------------------------------------------------

export const MOCK_DOCUMENTS: MentionItem[] = [
    { id: "doc_001", label: "Project_Specification.pdf" },
    { id: "doc_002", label: "Meeting_Notes.pdf" },
    { id: "doc_003", label: "Architecture_Overview.pdf" },
    { id: "doc_004", label: "API_Documentation.pdf" },
    { id: "doc_005", label: "User_Flow.pdf" },
    { id: "doc_006", label: "Product_Requirements.pdf" },
    { id: "doc_007", label: "Engineering_Guidelines.pdf" },
    { id: "doc_008", label: "Release_Checklist.pdf" },
    { id: "doc_009", label: "Integration_Guide.pdf" },
    { id: "doc_010", label: "Design_System.pdf" },
];
