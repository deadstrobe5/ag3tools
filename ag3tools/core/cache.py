import time
from typing import Any, Dict, Tuple

from ag3tools.core.settings import CACHE_ENABLED, CACHE_TTL_SECONDS


_store: Dict[Tuple[str, Tuple[Any, ...]], Tuple[float, Any]] = {}


def _now() -> float:
    return time.time()


def cache_get(key: str, *args: Any):
    if not CACHE_ENABLED:
        return None
    k = (key, args)
    entry = _store.get(k)
    if not entry:
        return None
    ts, value = entry
    if _now() - ts > CACHE_TTL_SECONDS:
        _store.pop(k, None)
        return None
    return value


def cache_set(key: str, value: Any, *args: Any):
    if not CACHE_ENABLED:
        return
    k = (key, args)
    _store[k] = (_now(), value)


def cache_clear():
    _store.clear()
