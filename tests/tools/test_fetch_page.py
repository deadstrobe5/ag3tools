from ag3tools import invoke_tool


def test_fetch_page_example():
    out = invoke_tool("fetch_page", url="https://example.com")
    assert out.status in (200, 301, 302)
    assert out.url.startswith("http")

