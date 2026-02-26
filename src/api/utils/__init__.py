"""
Token chunk buffer and event persistence helpers for streaming.

TokenChunkBuffer accumulates incoming token strings and flushes them as
grouped chunks to reduce database row counts while preserving full replay
capability.

Chunks are flushed when either threshold is reached (whichever comes first):
  - token_chunk_size  (default 50 chars)
  - token_chunk_flush_ms (default 200 ms since last flush)
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional

from src.api.constants import EVENT_TOKEN_CHUNK
from src.core.config import settings


@dataclass
class PendingChunk:
    """A token chunk ready to be persisted."""

    seq: int
    content: str
    event_type: str = EVENT_TOKEN_CHUNK
    metadata: Optional[dict] = None


class TokenChunkBuffer:
    """Accumulates streaming tokens and yields persistence-ready chunks.

    Usage::

        buf = TokenChunkBuffer(seq_start=3)
        for token in tokens:
            chunk = buf.add(token)
            if chunk:
                persist(chunk)
        # After streaming ends:
        final = buf.flush_final()
        if final:
            persist(final)

    The buffer does NOT manage its own async timer — the caller is responsible
    for periodically calling ``flush_if_stale()`` (e.g. via ``asyncio.create_task``).
    This keeps the buffer simple and testable.
    """

    def __init__(
        self,
        seq_start: int = 1,
        chunk_size: Optional[int] = None,
        flush_ms: Optional[int] = None,
    ):
        self._chunk_size = chunk_size or settings.token_chunk_size
        self._flush_ms = flush_ms or settings.token_chunk_flush_ms
        self._buffer: str = ""
        self._seq: int = seq_start
        self._last_flush_time: float = time.monotonic()

    @property
    def next_seq(self) -> int:
        """Return the next sequence number that will be assigned."""
        return self._seq

    @property
    def buffered_len(self) -> int:
        return len(self._buffer)

    def add(self, token: str) -> Optional[PendingChunk]:
        """Append a token. Returns a PendingChunk if size threshold is met."""
        if not token:
            return None
        self._buffer += token
        if len(self._buffer) >= self._chunk_size:
            return self._flush()
        return None

    def flush_if_stale(self) -> Optional[PendingChunk]:
        """Flush if time threshold exceeded and buffer is non-empty."""
        if not self._buffer:
            return None
        elapsed_ms = (time.monotonic() - self._last_flush_time) * 1000
        if elapsed_ms >= self._flush_ms:
            return self._flush()
        return None

    def flush_final(self) -> Optional[PendingChunk]:
        """Flush any remaining buffered text. Call once after streaming ends."""
        if not self._buffer:
            return None
        return self._flush()

    def _flush(self) -> PendingChunk:
        chunk = PendingChunk(seq=self._seq, content=self._buffer)
        self._seq += 1
        self._buffer = ""
        self._last_flush_time = time.monotonic()
        return chunk


class EventSequencer:
    """Thread-safe monotonic sequence counter for event persistence.

    Manages seq assignment for all event types within a single message
    generation. The TokenChunkBuffer has its own internal seq tracking;
    this sequencer coordinates seq values across ALL event types.
    """

    def __init__(self, start: int = 1):
        self._seq = start

    @property
    def current(self) -> int:
        return self._seq

    def next(self) -> int:
        """Return next seq and advance the counter."""
        seq = self._seq
        self._seq += 1
        return seq
