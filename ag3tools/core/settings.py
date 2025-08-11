import os


def _get_env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_env_float(name: str, default: float) -> float:
    val = os.getenv(name)
    try:
        return float(val) if val is not None else default
    except Exception:
        return default


def _get_env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    try:
        return int(val) if val is not None else default
    except Exception:
        return default


CACHE_ENABLED = _get_env_bool("AGTOOLS_CACHE_ENABLED", True)
CACHE_TTL_SECONDS = _get_env_int("AGTOOLS_CACHE_TTL", 900)  # 15 minutes

HTTP_TIMEOUT_SECONDS = _get_env_float("AGTOOLS_HTTP_TIMEOUT", 8.0)

# Cost logging
COST_LOG_ENABLED = _get_env_bool("AG3TOOLS_COST_LOG_ENABLED", True)
COST_LOG_PATH = os.getenv("AG3TOOLS_COST_LOG_PATH", os.path.expanduser("~/.ag3tools/cost_logs.jsonl"))
