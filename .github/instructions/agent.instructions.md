---
applyTo: "src/agents/**"
---

# LangGraph Agent — canonical patterns

> These rules apply to every file under `src/agents/`. They complement the
> cross-cutting rules in `.github/copilot-instructions.md`.

## State

- **Graph state** → `TypedDict` with `total=False`. All state types live in
  `src/agents/utils/state.py`. Never define graph state anywhere else.
- **Data models** → Pydantic `BaseModel`. Used for structured LLM output and
  inter-node data contracts.
- Never duplicate a model definition. If a model already exists in `state.py`,
  import it — do not redefine it.

```python
# ✅ correct
from src.agents.utils.state import State, FinalMCQ

# ❌ wrong — redefining in a node file
class FinalMCQ(BaseModel): ...
```

## Node signatures — dependency injection

Every node receives its dependencies as **parameters**, not as captured globals
or inline instantiations.

```python
# LLM node — LLM injected as parameter
async def planner_node(state: State, llm: BaseChatModel) -> dict:
    """Generate a test plan from the user intent.

    Args:
        state: Current graph state.
        llm: Language model to use for planning.

    Returns:
        Partial state update dict.
    """

# Service node — no LLM needed
async def retrieval_node(state: State) -> dict: ...

# Pure-compute node — sync is fine
def assemble_final_mcqs_node(state: State) -> dict: ...
```

The graph-level wrapper in `src/agents/chat_agent.py` closes over the injected
LLM — node files never reference `llm_config` directly:

```python
# chat_agent.py — the only place that wires LLMs to nodes
async def planner_graph_node(state: State) -> dict:
    return await planner_node(state, planner_llm)
```

## LLM configuration

All `ChatOpenAI` / `ChatOllama` instantiation lives **exclusively** in
`src/agents/utils/llm_config.py`. Node files and graph files import the
pre-configured instances — never call `ChatOpenAI(...)` inline.

```python
# ✅ correct
from src.agents.utils.llm_config import planner_llm

# ❌ wrong
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini")  # inline instantiation
```

## Prompt registry

Use the single `PROMPT_REGISTRY` in `src/agents/prompts/`. Each prompt module
(e.g. `classification.py`, `generation.py`) exports named `PromptTemplate`
instances. Do **not** add to the legacy `PROMPTS` dict in
`src/agents/utils/prompts.py`.

```python
# ✅ correct
from src.agents.prompts import PROMPT_REGISTRY
prompt = PROMPT_REGISTRY["scope_classifier"]

# ❌ wrong — legacy registry
from src.agents.utils.prompts import PROMPTS
```

## Helpers & utils — separation of concerns

| Responsibility                              | Location                         |
| ------------------------------------------- | -------------------------------- |
| Graph state types                           | `src/agents/utils/state.py`      |
| LLM instances & model config                | `src/agents/utils/llm_config.py` |
| Pure helper functions (formatting, parsing) | `src/agents/utils/helpers.py`    |
| Service integrations (retrieval, concepts)  | `src/agents/utils/services/`     |
| Prompt templates                            | `src/agents/prompts/`            |
| Node functions                              | `src/agents/nodes/`              |
| Graph assembly & routing                    | `src/agents/chat_agent.py`       |

Node files should contain **orchestration logic only**. Any reusable
formatting, data transformation, or validation belongs in `utils/helpers.py`
or a dedicated helper module — not duplicated across node files.

## Stream events

Every node must emit **both** `started` and `completed` events:

```python
writer = get_stream_writer()
writer({"event": "node_update", "node": "planner", "status": "started", "label": "Planning test..."})
# ... work ...
writer({"event": "node_update", "node": "planner", "status": "completed", "label": "Plan ready"})
```

Missing `completed` events leave the UI in an indeterminate state.

## Error handling

Wrap every `ainvoke()` call. Return a graceful fallback partial state rather
than letting the exception propagate and crash the graph run.

```python
# Follow the pattern in src/agents/nodes/retrieval.py
try:
    result = await llm.ainvoke(prompt)
except Exception as exc:
    logger.error("planner_node failed: %s", exc)
    return {"plan": None, "error": str(exc)}
```

## Config

Use `src/agents/config.py` — a Pydantic `BaseSettings` subclass reading `.env`.
No bare `os.getenv()` or `load_dotenv()` calls in any agent module.

```python
from src.agents.config import agent_settings

base_url = agent_settings.ollama_base_url  # ✅
os.getenv("OLLAMA_BASE_URL")               # ❌
```

## Logging

```python
import logging
logger = logging.getLogger(__name__)
```

No `print()`. No structlog.

## On-touch cleanup checklist

When you edit **any** file in `src/agents/`, also fix these in that same file:

- [ ] Replace `print(...)` with `logger.info/warning/error(...)`
- [ ] Add Google-style docstring to any touched public function or class
- [ ] Remove unused imports (e.g. `from ollama import generate` in `utils/prompts.py`)
- [ ] If touching `src/agents/utils/state.py`: remove duplicate `MCQOption` and
      `FinalMCQ` definitions (first definition at L87–L98 is dead, second at
      L110–L164 is canonical) and fix typo `retrived_context` → `retrieved_context`
- [ ] If touching `src/agents/nodes/generation/stem.py`: add missing `completed`
      stream event after LLM call
- [ ] If touching the legacy files below, delete them outright:
      `src/agents/main.py`, `src/agents/mcq.py`, `src/graph.py`, `prompts.py` (root)

## Known dead / legacy code — do not extend

| File                          | Status                                               |
| ----------------------------- | ---------------------------------------------------- |
| `src/agents/graph.py`         | Deprecated — replaced by `chat_agent.py`             |
| `src/agents/utils/nodes.py`   | Legacy class-based nodes — do not add new nodes here |
| `src/agents/utils/prompts.py` | Legacy prompt dict — use `PROMPT_REGISTRY`           |
| `src/agents/main.py`          | Stub — delete on next touch                          |
| `src/agents/mcq.py`           | Disconnected script — delete on next touch           |
