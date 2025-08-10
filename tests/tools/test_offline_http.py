import pytest
import httpx
from ag3tools import invoke_tool


@pytest.mark.parametrize(
    "status,body,ctype",
    [
        (200, "<html>ok</html>", "text/html"),
        (404, "not found", "text/plain"),
    ],
)
def test_fetch_page_offline(monkeypatch, status, body, ctype):
    class MockResponse:
        def __init__(self, url):
            self.url = url
            self.status_code = status
            self.headers = {"content-type": ctype}
            self.text = body

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def get(self, url, headers=None):
            return MockResponse(url)

    monkeypatch.setattr(httpx, "Client", MockClient)

    out = invoke_tool("fetch_page", url="https://offline.test")
    assert out.status == status
    assert out.content_type == ctype

