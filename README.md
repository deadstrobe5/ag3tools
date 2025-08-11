## ag3tools — composable tools for LLM agents

Small, framework-agnostic tools with typed IO, simple registry, adapters, and a clean CLI.

### Install
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[adapters]
```

### Quick use
- Find docs fast:
```python
from ag3tools.core.registry import invoke_tool
print(invoke_tool("find_docs", technology="langgraph"))
```
- CLI:
```bash
ag3tools docs langgraph              # heuristic
ag3tools docs langgraph --validate   # fetch + validate
ag3tools list                        # list tools
ag3tools run find_docs --kv technology=langgraph --json
```

### Modes (for find_docs)
- fast: heuristic rank
- validated: fetch + heuristic validate
- cracked: LLM re-rank + LLM validate

### Features
- Typed inputs/outputs (Pydantic)
- Self-registering tools (no __all__ busy-work)
- Adapters: OpenAI function-calling, LangChain
- In-memory cache for search (env-controlled)
- LLM cost logging (auto; JSONL)

### Config (env)
- AG3TOOLS_CACHE_ENABLED (default: true)
- AG3TOOLS_CACHE_TTL (seconds, default: 900)
- AG3TOOLS_HTTP_TIMEOUT (seconds, default: 8.0)
- AG3TOOLS_COST_LOG_ENABLED (default: true)
- AG3TOOLS_COST_LOG_PATH (default: ~/.ag3tools/cost_logs.jsonl)

### Tests
```bash
pytest -q               # all
pytest tests/core -q    # core & fast
pytest tests/tools -q   # tools
```

### Cookbook
Examples in `cookbook/`.

### Roadmap (short)
- CLI: flags for modes (`--mode`, `--top-k`, `--model`)
- CLI: `ag3tools costs summarize` (by tool/model/time)
- List output: show `llm_expected_tokens` and estimated $ using current pricing
