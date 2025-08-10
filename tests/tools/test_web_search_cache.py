import time
from ag3tools.tools.search.web_search import web_search
from ag3tools.core.types import WebSearchInput
from ag3tools.core.cache import cache_clear


def test_web_search_caching_speed(monkeypatch):
    cache_clear()
    q = WebSearchInput(query="langgraph", max_results=5)

    t0 = time.perf_counter()
    _ = web_search(q)
    t1 = time.perf_counter()

    _ = web_search(q)
    t2 = time.perf_counter()

    cold = t1 - t0
    warm = t2 - t1

    # Warm run should be significantly faster (at least 3x)
    assert warm * 3 < cold