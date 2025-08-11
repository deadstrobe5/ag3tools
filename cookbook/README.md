# Cookbook

Real-world examples of using ag3tools in different scenarios.

## Setup
```bash
# Create and activate venv (if not done)
python3 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e ..

# For LLM-powered tools
export OPENAI_API_KEY=...
```

## Examples

### example_find_docs.py
Shows how to use the documentation finder with different modes:
```bash
python example_find_docs.py
```
- Tests fast/validated/cracked modes
- Shows different project types:
  - New frameworks (langgraph)
  - Popular frameworks (fastapi)
  - Libraries (pydantic)
  - Complex docs (langchain)
- Demonstrates mode tradeoffs
