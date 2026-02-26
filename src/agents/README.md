# Agents

This directory contains LangGraph-based agent workflows used by Otis.

## Active Chat Graph

File: `src/agents/chat_agent.py`

```mermaid
flowchart TD
  START --> guardrail_node
  guardrail_node -->|ALLOW| query_generation_node
  guardrail_node -->|BLOCK| END
  query_generation_node --> retrieval_node
  retrieval_node --> generator_router
  generator_router -->|DEFAULT| chat_model
  generator_router -->|NAIVE| naive_mcq_generator_node
  chat_model --> END
  naive_mcq_generator_node --> END
```

### Purpose

- `guardrail_node`: intent/safety gate.
- `query_generation_node`: builds semantic search queries from user prompt + concept map.
- `retrieval_node`: strict doc-scoped vector retrieval with dedupe and cap.
- `chat_model`: default generation path, grounded by retrieved chunks.
- `naive_mcq_generator_node`: feature-flag path for fast MCQ iteration.

## Legacy Generation Graph

File: `src/agents/graph.py`

```mermaid
flowchart TD
  START --> fetch_documents
  fetch_documents --> generate_summaries
  generate_summaries --> human_approval
  human_approval --> generate_search_queries
  generate_search_queries --> retrieve_context
  retrieve_context --> END
```

This graph is still used by `/v1/graph/start` and `/v1/graph/resume` SSE endpoints.

## Runtime Configuration

Configured via `src/core/config.py`:

- `num_search_queries` (default `5`)
- `max_retrieved_chunks` (default `20`)
- `use_naive_mcq_generator` (default `False`)
- `chat_graph_retrieval_enabled` (default `True`)
- `chat_router_retrieval_fallback` (default `False`)
