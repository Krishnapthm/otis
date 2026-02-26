-- Migration: 003_chat_message_events
-- Description: Create chat_message_events table for persistent, resumable event streaming
-- Date: 2026-02-26
--
-- This table stores structured streaming events (thinking updates, token chunks,
-- reasoning tokens, lifecycle events) associated with assistant message generation.
--
-- Events are supplemental rendering/replay data — messages remain the authoritative
-- conversation state. Events enable:
--   - Resumable streaming (client reconnects with last-seen seq)
--   - Full replay of generation process for debugging / UI reconstruction
--   - Structured metadata storage without schema changes for new event types

CREATE TABLE IF NOT EXISTS chat_message_events (
    event_id        UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id      UUID            NOT NULL
                                    REFERENCES chat_messages(message_id) ON DELETE CASCADE,
    seq             INTEGER         NOT NULL CHECK (seq > 0),
    event_type      TEXT            NOT NULL,
    -- No CHECK constraint on event_type: new types can be introduced without DDL changes.
    -- Current conventions: started, thinking, token_chunk, reasoning_token, done, error
    content         TEXT,           -- Human-readable representation (token text, label, error detail)
    metadata        JSONB,          -- Arbitrary structured payload (tool I/O, citations, model id, etc.)
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),

    -- Enforce per-message monotonic sequencing
    CONSTRAINT uq_message_events_seq UNIQUE (message_id, seq)
);

-- Fast lookup of all events for a message, ordered by seq
CREATE INDEX IF NOT EXISTS idx_message_events_message_id
    ON chat_message_events (message_id);

-- Efficient range scan for replay: WHERE message_id = $1 AND seq > $2 ORDER BY seq
CREATE INDEX IF NOT EXISTS idx_message_events_message_seq
    ON chat_message_events (message_id, seq);

COMMENT ON TABLE  chat_message_events             IS 'Persistent streaming events linked to assistant messages. Supports replay and resumable SSE.';
COMMENT ON COLUMN chat_message_events.seq          IS 'Per-message monotonic integer (1, 2, 3…). Client resumes with (message_id, last_seq).';
COMMENT ON COLUMN chat_message_events.event_type   IS 'Event kind: started, thinking, token_chunk, reasoning_token, done, error. Extensible without DDL.';
COMMENT ON COLUMN chat_message_events.content      IS 'Primary human-readable content for the event (token text, thinking label, error detail).';
COMMENT ON COLUMN chat_message_events.metadata     IS 'Arbitrary JSONB payload: tool inputs/outputs, retrieval context, citations, model identifiers, finish reasons, etc.';
