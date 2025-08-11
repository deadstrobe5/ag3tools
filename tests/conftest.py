import contextlib
import time
from typing import Iterator

import pytest

from ag3tools.core.cache import cache_clear


@pytest.fixture(autouse=True)
def _fresh_env_and_cache(monkeypatch) -> Iterator[None]:
    # Ensure cache is enabled with short TTL for tests
    monkeypatch.setenv("AG3TOOLS_CACHE_ENABLED", "true")
    monkeypatch.setenv("AG3TOOLS_CACHE_TTL", "60")
    cache_clear()
    yield
    cache_clear()


@contextlib.contextmanager
def measure_time():
    t0 = time.perf_counter()
    yield lambda: time.perf_counter() - t0
