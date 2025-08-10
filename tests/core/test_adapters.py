from ag3tools import openai_tool_specs_from_registry, langchain_tools_from_registry


def test_openai_specs_present():
    specs = openai_tool_specs_from_registry()
    names = {s["function"]["name"] for s in specs}
    assert {"find_docs", "web_search", "rank_docs"}.issubset(names)


def test_langchain_tools_present():
    tools = langchain_tools_from_registry()
    names = {t.name for t in tools}
    assert {"find_docs", "web_search", "rank_docs"}.issubset(names)

