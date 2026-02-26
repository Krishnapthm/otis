# Otis Agent Flows

## Chat Invoke Flow

```mermaid
flowchart TD
  A[User Prompt + Mentioned Doc IDs] --> B[guardrail_node]
  B -->|ALLOW| C[query_generation_node]
  B -->|BLOCK| Z[END]
  C --> D[retrieval_node]
  D --> E{Generator Route}
  E -->|default| F[chat_model]
  E -->|naive flag| G[naive_mcq_generator_node]
  F --> Z
  G --> Z
```

## Generation SSE Flow

```mermaid
flowchart TD
  A[/v1/graph/start] --> B[fetch_documents]
  B --> C[generate_summaries]
  C --> D[human_approval interrupt]
  D --> E[/v1/graph/resume]
  E --> F[generate_search_queries]
  F --> G[retrieve_context]
  G --> H[END]
```

## Notes

- Chat retrieval is executed inside LangGraph deterministic nodes.
- Guardrail and intent routing are unchanged.
- Mentioned document IDs are passed from frontend invoke state to backend graph state.
