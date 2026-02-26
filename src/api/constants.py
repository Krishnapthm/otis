"""
Event type constants for chat_message_events.

New event types can be added here without any schema or DDL changes.
The event_type column has no CHECK constraint — these are conventions only.
"""

# Lifecycle events
EVENT_STARTED = "started"
EVENT_DONE = "done"
EVENT_ERROR = "error"

# Streaming content events
EVENT_TOKEN_CHUNK = "token_chunk"
EVENT_REASONING_TOKEN = "reasoning_token"

# Agent observability events
EVENT_THINKING = "thinking"

# Future-ready event types (uncomment when needed)
# EVENT_TOOL_CALL = "tool_call"
# EVENT_TOOL_RESULT = "tool_result"
# EVENT_RETRIEVAL_TRACE = "retrieval_trace"
# EVENT_CITATION = "citation"
