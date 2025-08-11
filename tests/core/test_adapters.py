import ag3tools


def test_openai_specs_present():
    specs = ag3tools.get_openai_tools()
    names = {s["function"]["name"] for s in specs}
    assert {"find_docs", "web_search", "rank_docs"}.issubset(names)


def test_langchain_tools_present():
    tools = ag3tools.get_langchain_tools()
    names = {t.name for t in tools}
    assert {"find_docs", "web_search", "rank_docs"}.issubset(names)
