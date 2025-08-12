# 🤖 ag3tools

**Zero-maintenance LLM tool library**

[![Tests](https://img.shields.io/badge/tests-17%2F17%20passing-brightgreen)](#) [![Python](https://img.shields.io/badge/python-3.9%2B-blue)](#)

*Tiny, composable tools for LLM agents with auto-discovery, typed I/O, and cost tracking*

## ✨ Features

- **🔧 Zero Maintenance** — Add tools without touching imports
- **📝 Type Safe** — Full Pydantic validation
- **🌐 Framework Agnostic** — Works with OpenAI, LangChain, anything
- **⚡ Smart Caching** — Built-in caching with TTL
- **💰 Cost Tracking** — Automatic LLM cost logging with analytics

## 🚀 Quick Start

```bash
pip install -e .
```

```python
import ag3tools

# Find docs
docs_url = ag3tools.find_docs_url("fastapi")

# Search web
results = ag3tools.invoke_tool("web_search", query="python", max_results=5)

# List tools
tools = ag3tools.list_tools()
```

```bash
# CLI usage
ag3tools list
ag3tools docs fastapi
ag3tools run web_search --kv query="test"
```

## 🛠️ Available Tools

- **Search**: `web_search`, `web_search_async`
- **Docs**: `find_docs`, `rank_docs`, `validate_docs_*`
- **Net**: `fetch_page`, `fetch_page_async`
- **Smithery**: Import any MCP server from [smithery.ai](https://smithery.ai)

## 🔌 Integrations

```python
# OpenAI
tools = ag3tools.get_openai_tools()
result = ag3tools.run_openai_tool_call(tool_call)

# LangChain
tools = ag3tools.get_langchain_tools()

# Smithery MCP Servers
from ag3tools.tools.smithery import import_smithery_server
import_smithery_server("@nickclyde/duckduckgo-mcp-server")
result = ag3tools.invoke_tool("smithery:@nickclyde/duckduckgo-mcp-server:search", query="python")
```

## ➕ Adding Tools

```python
# File: ag3tools/tools/category/my_tool.py
from pydantic import BaseModel, Field
from ag3tools.core.registry import register_tool

class MyInput(BaseModel):
    query: str = Field(..., description="Query string")

@register_tool(
    description="Does something useful",
    input_model=MyInput,
    tags=["utility"],
)
def my_tool(input: MyInput):
    return {"result": f"processed: {input.query}"}

# That's it! Auto-discovered, no imports needed.
```

## 💰 Cost Tracking & Analytics

All LLM tool calls are automatically logged with detailed cost and token usage data:

```bash
# View cost overview
ag3tools costs

# Analyze specific tool
ag3tools costs --tool validate_docs_llm

# View recent trends  
ag3tools costs --days 7

# Export to CSV for analysis
python scripts/analyze_costs.py --export costs.csv
```

Cost logs are stored in `data/cost_logs/` with daily files containing:
- Token usage (input/output)
- Actual costs (per model pricing)
- Execution times
- Tool parameters
- Model information

## ⚙️ Config

```bash
export AG3TOOLS_CACHE_ENABLED=true
export AG3TOOLS_CACHE_TTL=900
export AG3TOOLS_COST_LOG_ENABLED=true
export OPENAI_API_KEY=sk-...
```

## 🧪 Testing

```bash
pytest                 # all tests
pytest tests/core -q   # core only
```

---
