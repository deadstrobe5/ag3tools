from ag3tools import invoke_tool


def test_find_docs_many_basic():
    outs = invoke_tool("find_docs_many", technologies=["langgraph", "fastapi"])
    assert isinstance(outs, list)
    assert len(outs) == 2
    assert all(hasattr(o, "url") for o in outs)

