import pytest
from ag3tools import list_tools, invoke_tool


def test_registry_lists_tools():
    tools = list_tools()
    names = {t.name for t in tools}
    assert {"web_search", "rank_docs", "find_docs"}.issubset(names)


def test_invoke_tool_simple():
    out = invoke_tool("find_docs", technology="langgraph")
    assert hasattr(out, "url")

