## ag3tools — Tiny, composable tool library for LLM agents

A collection of modular, framework-agnostic tools that can be easily integrated with any LLM agent framework.

### Quick Start
```bash
# Install
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Use any tool directly
from ag3tools.core.registry import invoke_tool

# Find documentation
result = invoke_tool("find_docs", technology="langgraph")

# Or via CLI
ag3tools list                        # see available tools
ag3tools run find_docs --kv technology=langgraph
```

### Features
- Modular tools with typed IO (Pydantic)
- Self-registering tool registry
- Framework adapters:
  - OpenAI function calling
  - LangChain tools
- Built for agents:
  - Clean tool discovery
  - Automatic cost logging
  - Smart caching
  - Async variants

### Available Tools
- Documentation tools:
  - `find_docs`: Find official docs (fast/validated/cracked modes)
  - `validate_docs`: Check if page is real documentation
  - `rank_docs`: Score and rank documentation candidates
- Search tools:
  - `web_search`: Clean web search results
  - `web_search_async`: Non-blocking variant
- Network tools:
  - `fetch_page`: Get page content with validation
  - `fetch_page_async`: Non-blocking variant

### Config
Control via environment:
```bash
# LLM features
export OPENAI_API_KEY=...            # for LLM-powered tools
export AG3TOOLS_LLM_MODEL=gpt-4o-mini  # optional override

# Caching
export AG3TOOLS_CACHE_ENABLED=true   # default
export AG3TOOLS_CACHE_TTL=900       # seconds

# Cost logging
export AG3TOOLS_COST_LOG_ENABLED=true  # default
export AG3TOOLS_COST_LOG_PATH=~/.ag3tools/cost_logs.jsonl
```

### Examples
See `cookbook/` for real usage examples of different tools and modes.

### Tests
```bash
pytest -q               # all tests
pytest tests/core -q    # core & fast
pytest tests/tools -q   # tools only
```
