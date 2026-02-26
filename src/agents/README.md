# Agents

This directory contains LangGraph-based agent workflows used by Otis.

## Active Chat Graph

File: `src/agents/chat_agent.py`

```mermaid
flowchart TD
  START --> scope_classifier
  scope_classifier -->|ALLOW| intent_classifier
  scope_classifier -->|BLOCK| END

  intent_classifier -->|mcq_request/followup| planner
  intent_classifier -->|utility_task| chat_tools
  intent_classifier -->|clarification| chat_model

  planner -->|edit_strategy=patch| chat_tools
  planner -->|edit_mode && retrieval_signature_valid*| dispatch_questions
  planner -->|otherwise| retrieval

  retrieval --> dispatch_questions
  dispatch_questions --> question_subgraph_runner
  question_subgraph_runner --> assemble_final_output
  assemble_final_output --> finalize_metadata
  finalize_metadata --> chat_model

  chat_tools -->|artifact_bump=true| finalize_metadata
  chat_tools -->|otherwise| chat_model
  chat_model --> END
```

### Purpose

- `scope_classifier`: binary scope/safety gate (ALLOW/BLOCK).
- `intent_classifier`: routes request to MCQ planning, tools, or clarification reply.
- `planner`: produces MCQ plan and edit-mode controls.
- `retrieval`: retrieves chunks from doc-scoped context.
- `dispatch_questions`: fans out per question via Send API.
- `question_subgraph_runner`: runs isolated per-question generation+validation subgraph.
- `assemble_final_output`: sorts by `question_index` and builds final MCQ output.
- `finalize_metadata`: bumps `artifact_version` when required.
- `chat_tools`: placeholder branch for utility tools / patch strategy.
- `chat_model`: final response synthesis node.

\* `retrieval_signature_valid` is a placeholder gate for skip-retrieval behavior.

### Per-Question Subgraph

File: `src/agents/mcq_subgraph.py`

```mermaid
flowchart TD
  START --> stem_generator
  stem_generator --> options_generator
  stem_generator --> distractor_generator
  options_generator --> validator
  distractor_generator --> validator
  validator -->|pass| finalize_draft
  validator -->|retry_count < max| stem_generator
  validator -->|retry_count >= max| finalize_draft
  finalize_draft --> END
```

Subgraph state is isolated per question. Retries do not affect other question instances.

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

## Placeholder Notes

- `patch_mcq` tool behavior is scaffolded but not fully implemented.
- Retrieval validity signature (`retrieval_signature` / `retrieval_signature_valid`) is scaffolded.
- Artifact versioning is state-level placeholder (no dedicated DB persistence contract yet).
