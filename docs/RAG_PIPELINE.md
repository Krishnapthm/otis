# RAG Pipeline Reference

## Overview

Two retrieval paths share a common ingestion backbone. All canonical logic lives
in `src/rag/`; files in `src/services/`, `src/agents/utils/services/`, and
`src/tasks/` are thin re-export shims kept for backwards compatibility.

---

## Embedding Model

| Property | Value                                                     |
| -------- | --------------------------------------------------------- |
| Model    | `nomic-embed-text`                                        |
| Provider | Ollama (self-hosted, no external API)                     |
| Library  | `langchain-ollama` (`OllamaEmbeddings`)                   |
| Endpoint | `OLLAMA_BASE_URL` env var → default `http://ollama:11434` |

Used at both ingest time (chunk + concept embeddings) and query time.

---

## Vector Store

| Property   | Value                                                     |
| ---------- | --------------------------------------------------------- |
| Backend    | PostgreSQL + pgvector (`langchain-postgres` / `PGVector`) |
| Connection | `RETRIEVAL_DATABASE_URL` env var                          |
| Similarity | Cosine (`<=>` operator)                                   |
| Namespace  | Per-user collection: `user_{user_id}`                     |

**Tables:**

- `langchain_pg_embedding` — chunk vectors
- `langchain_pg_collection` — one row per user namespace
- `document_concepts` — concept-level embeddings (custom, also pgvector)
- `user_vectorstore` — tracks job_id, sync status, last_synced_at

---

## Chunking Strategy

Two-stage hierarchical split (`src/rag/tasks.py:185-211`, `src/rag/embedding.py`):

**Stage 1 — Structure-aware (Markdown heading hierarchy)**

```python
MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "heading"), ("##", "section"), ("###", "subsection")],
    strip_headers=False   # preserves headings inside chunks
)
```

**Stage 2 — Size-based (applied only to chunks > 800 chars)**

```python
RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100, add_start_index=True)
```

Chunk metadata: `user_id`, `document_id`, `source`, `file_name`.

---

## Ingestion Pipeline (`src/rag/tasks.py`)

```
Upload (≤60 MB, pdf/txt/doc/docx/md)
  → stream to .staging dir, compute file SHA-256
  → duplicate check (is_embedded flag)
  → enqueue RQ job (Redis, 2h timeout)

RQ Worker:
  1. pymupdf4llm.to_markdown()       # layout-aware PDF → Markdown
  2. content_hash check              # skip re-embedding identical content
  3. extract_concepts() [gpt-4.1-nano] → 3–10 (name, summary) pairs
  4. MarkdownHeaderTextSplitter      # split on headings
  5. RecursiveCharacterTextSplitter  # split oversized chunks (>800 chars)
  6. OllamaEmbeddings + PGVector.add_documents()
  7. store_concepts()                # embed summaries → document_concepts table
  8. document.is_embedded = True, status = "ready"
```

---

## Retrieval — Chat Path (`src/rag/retrieval.py`)

Concept-aware two-layer retrieval:

**Layer 1 — Concept matching (document_concepts table)**

```sql
SELECT concept_name, concept_summary,
       1 - (concept_embedding <=> :query_vec) AS score
FROM document_concepts
WHERE document_id IN (:ids)
ORDER BY concept_embedding <=> :query_vec
LIMIT 3   -- CONCEPT_TOP_K
```

Threshold: `score >= 0.3`. Falls back to plain search if no concept qualifies.

**Layer 2 — Augmented chunk retrieval**

```python
search_query = f"{query}\n\nRelevant topics: {concept_summaries}"
PGVector.as_retriever(filter={"document_id": ...}, k=20).invoke(search_query)
```

Dedup: first 200 chars of chunk content used as key. Returns top-20 chunks.

---

## Retrieval — Agent / MCQ Path (`src/rag/agent_retrieval.py`)

Multi-query similarity search:

1. Planner LLM (`gpt-4.1-nano`) emits `retrieval_queries: List[str]` (up to 5).
2. Each query run independently:
   ```python
   PGVector.similarity_search_with_relevance_scores(
       query, k=20, filter={"document_id": {"$in": doc_ids}}
   )
   ```
3. Results merged, sorted by cosine score desc, deduplicated by chunk SHA-256.
4. Top-20 chunks injected into generation nodes.

No reranking step; no BM25/hybrid search.

---

## Key Configuration (`src/core/config.py`)

| Setting                   | Value          |
| ------------------------- | -------------- |
| `max_retrieved_chunks`    | 20             |
| `num_search_queries`      | 5              |
| `CONCEPT_TOP_K`           | 3              |
| `CONCEPT_SCORE_THRESHOLD` | 0.3            |
| Chunk size                | 800 chars      |
| Chunk overlap             | 100 chars      |
| Concept / planner LLM     | `gpt-4.1-nano` |
| Max upload size           | 60 MB          |
| RQ job timeout            | 2 hours        |

---

## What Is Not Present

- No BM25 / hybrid (keyword + vector) search
- No HyDE (Hypothetical Document Embedding)
- No reranking (cross-encoder or otherwise)
- Chunk-to-concept tagging (`classify_chunks_to_concepts`) is defined in
  `src/rag/concepts.py` but not yet wired into the active ingestion loop
- MMR retriever exists in `src/rag/embedding.py` but is not used on active paths
