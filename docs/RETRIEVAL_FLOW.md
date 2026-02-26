# Two-Layer Concept-Aware Retrieval

> Architecture documentation for the concept extraction and retrieval system in Otis.

---

## Overview

Otis uses a **two-layer retrieval** system that combines semantic concept matching with vector chunk search to deliver precise, document-scoped context to the chat LLM.

When a user tags documents in a chat message (via the mention picker), the system:

1. **Layer 1 — Concept Matching:** Finds which high-level concepts from those documents are most relevant to the query.
2. **Layer 2 — Chunk Retrieval:** Searches the vector store for chunks scoped to the mentioned documents, using matched concept summaries to augment the search query for better semantic targeting.

This approach gives the LLM focused, topically coherent context without requiring concept metadata on individual chunks.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DOCUMENT UPLOAD                              │
│                                                                     │
│  Upload API ──► store_file() ──► upload_new_doc() ──► DB row        │
│                                   (status=pending)                  │
│                                                                     │
│  Embeddings Sync ──► RQ Queue ──► process_user_embeddings()         │
│                                        │                            │
│                                        ▼                            │
│                               ┌────────────────┐                    │
│                               │  Docling Parse  │                   │
│                               │  file → markdown│                   │
│                               └───────┬────────┘                    │
│                                       │                             │
│                          ┌────────────┼────────────┐                │
│                          ▼            ▼            ▼                │
│                   ┌──────────┐ ┌───────────┐ ┌──────────────┐       │
│                   │ Extract  │ │  Chunk    │ │   Content    │       │
│                   │ Concepts │ │  (header  │ │   Dedup      │       │
│                   │ (gpt-4.1 │ │  + recur- │ │   Check      │       │
│                   │  -nano)  │ │  sive)    │ │              │       │
│                   └────┬─────┘ └─────┬─────┘ └──────────────┘       │
│                        │             │                              │
│                    ┌───┴─────────────┴───┐                          │
│                    ▼                     ▼                          │
│          ┌──────────────┐  ┌─────────────────┐                      │
│          │ PGVector     │  │ document_       │                      │
│          │ add_documents│  │ concepts table  │                      │
│          │ (chunks +    │  │ (concept name + │                      │
│          │  embeddings) │  │  summary +      │                      │
│          └──────────────┘  │  embedding)     │                      │
│                            └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        CHAT QUERY                                   │
│                                                                     │
│  User sends message with @doc mentions                              │
│  POST /v1/chats/{chat_id}/invoke { message, doc_ids }               │
│                                                                     │
│            ┌──────────────────────────────────┐                     │
│            │    retrieve_with_concepts()       │                     │
│            │                                   │                     │
│            │  ┌─────────────────────────┐     │                     │
│            │  │  LAYER 1: Concept Match │     │                     │
│            │  │                         │     │                     │
│            │  │  embed(query)           │     │                     │
│            │  │       │                 │     │                     │
│            │  │       ▼                 │     │                     │
│            │  │  SELECT concept_name    │     │                     │
│            │  │  FROM document_concepts │     │                     │
│            │  │  WHERE doc_id IN (...)  │     │                     │
│            │  │  ORDER BY similarity    │     │                     │
│            │  │  LIMIT 3               │     │                     │
│            │  └──────────┬──────────────┘     │                     │
│            │             │                     │                     │
│            │             ▼                     │                     │
│            │  ┌─────────────────────────┐     │                     │
│            │  │  LAYER 2: Chunk Search  │     │                     │
│            │  │                         │     │                     │
│            │  │  PGVector retriever     │     │                     │
│            │  │  filter: {              │     │                     │
│            │  │    document_id: $in     │     │                     │
│            │  │  }                      │     │                     │
│            │  │  query augmented with   │     │                     │
│            │  │  concept summaries      │     │                     │
│            │  │  k=15                   │     │                     │
│            │  └──────────┬──────────────┘     │                     │
│            │             │                     │                     │
│            │             ▼                     │                     │
│            │    deduplicate + cap at 15        │                     │
│            └──────────────┬───────────────────┘                     │
│                           │                                         │
│                           ▼                                         │
│               ┌─────────────────────┐                               │
│               │  Inject as system   │                               │
│               │  message into       │                               │
│               │  input_state        │                               │
│               └─────────┬───────────┘                               │
│                         │                                           │
│                         ▼                                           │
│               ┌─────────────────────┐                               │
│               │  Chat Graph         │                               │
│               │  guardrail → LLM    │                               │
│               └─────────┬───────────┘                               │
│                         │                                           │
│                         ▼                                           │
│               SSE stream response to frontend                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### `document_concepts` table

| Column              | Type        | Description                                        |
| ------------------- | ----------- | -------------------------------------------------- |
| `concept_id`        | UUID (PK)   | Auto-generated primary key                         |
| `document_id`       | UUID (FK)   | References `documents.doc_id`, CASCADE on delete   |
| `concept_name`      | TEXT        | Short concept name (2-5 words)                     |
| `concept_summary`   | TEXT        | One-sentence summary (max 15 words)                |
| `concept_embedding` | VECTOR(768) | Embedding of `concept_summary` (nomic-embed-text)  |
| `extractor_version` | TEXT        | Version tag for cache invalidation (default: `v1`) |
| `created_at`        | TIMESTAMP   | Row creation time                                  |

**Constraints:**

- `UNIQUE(document_id, concept_name)` — one concept name per document
- IVFFlat index on `concept_embedding` for ANN search

**Migration:** `migrations/002_document_concepts.sql`

### Chunk metadata (in `langchain_pg_embedding.cmetadata` JSONB)

Chunk metadata contains the standard fields — no concept tags are stored on chunks:

```json
{
  "user_id": "abc-123",
  "document_id": "def-456",
  "source": "/uploads/lecture.pdf",
  "file_name": "lecture.pdf"
}
```

Concept awareness is achieved at query time via the `document_concepts` table (Layer 1), not via chunk metadata filtering.

```

---

## Components

### 1. Concept Extraction Service

**File:** `src/services/concept_service.py`

Two functions are called from the embedding worker:

| Function                       | Purpose                                                    |
|--------------------------------|------------------------------------------------------------|
| `extract_concepts()`          | LLM call (gpt-4.1-nano) to extract 3-10 concepts from full markdown |
| `store_concepts()`            | Embeds concept summaries and upserts into `document_concepts`       |

A third function, `classify_chunks_to_concepts()`, exists in the module but is **not currently wired into the pipeline**. It can be enabled later to tag individual chunks with concept names in their metadata for finer-grained filtering.

**Model:** `gpt-4.1-nano` (configurable via `CONCEPT_LLM_DEPLOYMENT` env var).

**Error handling:** All three functions are non-fatal. If any fail, the embedding pipeline continues without concept tagging — retrieval falls back to pure similarity search.

### 2. Two-Layer Retrieval Service

**File:** `src/services/retrieval_service.py`

| Function                    | Purpose                                                           |
|-----------------------------|-------------------------------------------------------------------|
| `retrieve_with_concepts()` | Main entry point — runs both layers and returns deduplicated docs |
| `format_retrieved_context()` | Formats docs into a context string for LLM injection            |

**Configuration constants:**

| Constant                  | Default | Description                            |
|---------------------------|---------|----------------------------------------|
| `CONCEPT_TOP_K`           | 3       | Max concepts to match in Layer 1       |
| `CONCEPT_SCORE_THRESHOLD` | 0.3     | Min cosine similarity for concept match|
| `MAX_CHUNKS`              | 15      | Total cap on retrieved chunks          |

### 3. Embedding Pipeline Integration

**File:** `src/tasks/embedding_tasks.py` — `process_user_embeddings()`

Two insertion points in the existing flow:

1. **After markdown extraction** (after Docling converts to markdown):
   - Calls `extract_concepts(md, doc_name)` to get the concept list.

2. **After `vector_store.add_documents()`**:
   - Calls `store_concepts(document_id, concepts, embeddings, db)` to persist concepts with their vector embeddings.

### 4. Chat Invoke Integration

**File:** `src/api/v1/routers/chat.py` — `invoke_chat_endpoint()`

**Insertion point:** After `input_state` is built, before the `stream()` generator runs.

**Logic:**
1. If `payload.doc_ids` is non-empty, instantiate `OllamaEmbeddings`.
2. Call `retrieve_with_concepts()` with the query, doc_ids, and user_id.
3. Format the retrieved chunks with `format_retrieved_context()`.
4. Prepend a system message with the context to `input_state["chat_messages"]`.
5. The existing chat graph (guardrail → LLM) receives context-augmented messages.

---

## Data Flow: End-to-End

### Upload → Embed → Concept Extract

```

1. User uploads file via POST /v1/documents/
2. File is stored, SHA-256 computed, Documents row created (status=pending)
3. User triggers POST /v1/embeddings/sync
4. RQ worker picks up job: process_user_embeddings()
5. Docling converts file → markdown, stores content_md on document row
6. Content-hash dedup check (existing logic, unchanged)
7. ★ NEW: extract_concepts(md) → list of {name, summary}
8. MarkdownHeaderTextSplitter + RecursiveCharacterTextSplitter → chunk list
9. OllamaEmbeddings embeds chunks → PGVector.add_documents()
10. ★ NEW: store_concepts() → embeds concept summaries → upserts to document_concepts
11. Document marked as is_embedded=True, status=ready

```

### Chat → Retrieve → Respond

```

1. User sends message with @doc mentions
   POST /v1/chats/{chat_id}/invoke { message: "explain eigenvalues", doc_ids: [...] }
2. User message + doc_ids stored in DB (existing logic, unchanged)
3. ★ NEW: retrieve_with_concepts() is called:
   a. Query is embedded via OllamaEmbeddings
   b. Layer 1: SELECT concept_name, concept_summary FROM document_concepts
   WHERE document_id IN (...) ORDER BY similarity → top 3 concepts
   c. Layer 2: PGVector retriever with filter:
   { document_id: $in(doc_ids) }
   query augmented with matched concept summaries
   → up to 15 chunks
   d. Deduplicate → max 15 chunks
4. ★ NEW: Context injected as system message:
   input_state = {
   chat_messages: [
   { role: "system", content: "Use the following context..." },
   { role: "user", content: "explain eigenvalues" }
   ]
   }
5. Chat graph runs: guardrail → chat_model (existing logic, unchanged)
6. SSE stream response to frontend (existing logic, unchanged)

```

---

## Fallback Behavior

The system is designed to degrade gracefully at every level:

| Failure Point                        | Behavior                                           |
|--------------------------------------|----------------------------------------------------|
| Concept extraction fails (LLM error) | Chunks embed normally; Layer 1 returns no concepts → query-only retrieval |
| Concept storage fails                | Chunks are embedded normally; Layer 1 finds no concepts → falls back      |
| Layer 1 finds no matching concepts   | Layer 2 runs with doc_id filter only, query not augmented                 |
| Layer 2 retrieval fails              | Chat proceeds without context (existing behavior)                         |
| No doc_ids in chat message           | No retrieval attempted; chat runs as plain LLM (existing behavior)        |

---

## Configuration

### Environment Variables

| Variable                   | Default                      | Description                                |
|----------------------------|------------------------------|--------------------------------------------|
| `CONCEPT_LLM_DEPLOYMENT`   | `gpt-4.1-nano`              | Azure OpenAI deployment for concept extraction |
| `CONCEPT_LLM_API_VERSION`  | `2024-12-01-preview`        | API version for concept LLM               |
| `OLLAMA_BASE_URL`          | `http://ollama:11434`       | Ollama server for embeddings               |
| `RETRIEVAL_DATABASE_URL`   | Falls back to `REDIS_DATABASE_URL` | PGVector connection for retrieval   |

### Tuning

The retrieval quality can be tuned by adjusting constants in `src/services/retrieval_service.py`:

- **`CONCEPT_TOP_K`** — More concepts = broader recall, less precision. Start with 3.
- **`CONCEPT_SCORE_THRESHOLD`** — Lower threshold = more concepts pass, risking noise. 0.3 is conservative.
- **`MAX_CHUNKS`** — Hard cap on total context size. 15 chunks ≈ ~12k chars ≈ ~3k tokens.

---

## Embedding Model Dependency

The current embedding model is **nomic-embed-text** (768 dimensions) running on Ollama. Both chunk embeddings and concept embeddings use the same model.

**If you switch embedding models:**

1. Alter `document_concepts.concept_embedding` column dimension.
2. Re-run concept embedding for existing documents (query `document_concepts`, re-embed summaries).
3. Re-embed all chunks (existing process — clear vectorstore + re-sync).
4. The concept extraction LLM (gpt-4.1-nano) is **independent** of the embedding model and does not need changes.

Since concept rows are lightweight (~5 per document), re-embedding the concept index is fast.

---

## Files Changed

| File | Change |
|------|--------|
| `migrations/002_document_concepts.sql` | **New** — Creates `document_concepts` table |
| `src/api/db/models/__init__.py` | Added `DocumentConcept` ORM model + relationship on `Documents` |
| `src/api/db/schema.py` | Added `DocumentConceptResponse`, `ConceptMatchResult` schemas |
| `src/services/concept_service.py` | **New** — Concept extraction, concept storage (chunk classification available but unused) |
| `src/services/retrieval_service.py` | **New** — Two-layer retrieval + context formatting |
| `src/tasks/embedding_tasks.py` | Wired concept extraction into the embedding pipeline |
| `src/api/v1/routers/chat.py` | Wired retrieval into the chat invoke endpoint |
| `src/agents/graph.py` | Marked as deprecated (to be deleted) |
```
