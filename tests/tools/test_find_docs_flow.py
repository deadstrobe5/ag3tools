from ag3tools import invoke_tool


def test_find_docs_and_validated():
    base = invoke_tool("find_docs", technology="langgraph")
    assert base.url

    val = invoke_tool("find_docs_validated", technology="langgraph")
    assert val.url

