## ag3tools — Tiny, composable agent tools

A small, framework-agnostic tool library for LLM agents. Clean IO models (Pydantic), minimal functions, easy adapters.

### Features
- Simple, single-responsibility tools
- Typed inputs/outputs for safe tool-calling
- Adapters for OpenAI tool-calling and LangChain
- CLI for quick usage
- Optional caching and page validation

### Install
Local editable install:

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[adapters]
```

Or install in another project (plug-and-play):

```
pip install -e /absolute/path/to/Ag3nts
```

### Quickstart

```python
from ag3tools import find_docs, FindDocsInput
print(find_docs(FindDocsInput(technology="langgraph")).url)
```

Zero-boilerplate (no input model import):
```python
from ag3tools import invoke_tool
print(invoke_tool("find_docs", technology="langgraph"))
```

One-liner convenience API:
```python
from ag3tools import find_docs_url
print(find_docs_url("langgraph"))
```

CLI:

```
ag3tools docs langgraph              # find docs for a technology
ag3tools docs langgraph --validate   # fetch + validate page content
ag3tools list                        # list all tools + descriptions  
ag3tools run find_docs --kv technology=langgraph --json
```

### Tools (organized)
- search: `ag3tools/tools/search/web_search.py`
- docs: `ag3tools/tools/docs/`
  - `rank_docs`, `find_docs`, `find_docs_validated`, `find_docs_many`
- generic: `fetch_page`, `validate_docs_page`

### Adapters
- OpenAI tool-calling
  ```python
  from openai import OpenAI
  from ag3tools import openai_tool_specs_from_registry, run_openai_tool_call_from_registry

  client = OpenAI()
  tools = openai_tool_specs_from_registry()
  messages = [{"role": "user", "content": "Find the docs for langgraph"}]
  resp = client.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools)
  for tc in resp.choices[0].message.tool_calls or []:
      out = run_openai_tool_call_from_registry(tc)
      messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": str(out)})
  ```

- LangChain
  ```python
  from ag3tools import langchain_tools_from_registry
  tools = langchain_tools_from_registry()
  ```

### Tags
- Each tool can have tags (e.g., `docs`, `search`, `net`, `async`, `validation`, `ranking`, `batch`).
- List with tags:
  - `ag3tools list`
  - `ag3tools list --tag docs` (filter)
  - `ag3tools list --json` (structured with tags)

### Async
- Call tools without blocking via `invoke_tool_async`:
  ```python
  import asyncio
  from ag3tools.core.registry import invoke_tool_async

  async def main():
      out = await invoke_tool_async("find_docs", technology="langgraph")
      print(out.url)
  asyncio.run(main())
  ```
- Some tools have async variants, e.g., `web_search_async`, `fetch_page_async`.

### Config (simple idea)
- Keep env-first config (already supported):
  - `AG3TOOLS_CACHE_ENABLED`, `AG3TOOLS_CACHE_TTL`, `AG3TOOLS_HTTP_TIMEOUT`
- A small `Config` object can be added later to override env at runtime (e.g., provider choice, timeouts, cache on/off) without changing the global env.
  - Pattern: `Config.from_env().with_overrides(cache_enabled=False, timeout=5.0)`

### Extend
- Add tools under `ag3tools/tools/` and register with `@register_tool(input_model=..., description=...)`.
- Define IO models in `ag3tools/types.py`.
- Tools get listed automatically via the registry.

### Caching (simple explainer)
- The library includes a tiny in-memory cache (`ag3tools/cache.py`). It stores results for a short time (default 15 minutes).
- Currently used in `web_search` so repeated queries in the same process are fast.
- Control via env vars:
  - `AG3TOOLS_CACHE_ENABLED=true|false` (default true)
  - `AG3TOOLS_CACHE_TTL=900` (seconds)
  - `AG3TOOLS_HTTP_TIMEOUT=8.0` (seconds)
- It’s intentionally simple: per-process, no persistence. You can disable it anytime.

### Tests
- Fast core tests: `pytest tests/core -q`
- Tool tests: `pytest tests/tools -q`
- All (default skips slow): `pytest -q`
- Mark slow tests with `@pytest.mark.slow` and run with: `pytest -m slow`

### Example
See `examples_find_docs.py`.


