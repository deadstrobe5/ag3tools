from ag3tools import invoke_tool


def test_validate_docs_positive():
    content = """
    <html><body>
    <div class="sidebar">Table of Contents</div>
    <input placeholder="Search docs" />
    API Reference
    </body></html>
    """
    out = invoke_tool("validate_docs_page", url="https://example.com/docs", content=content)
    assert out.is_docs


def test_validate_docs_negative():
    content = "<html><body>Hello world</body></html>"
    out = invoke_tool("validate_docs_page", url="https://example.com/", content=content)
    assert out.is_docs is False

