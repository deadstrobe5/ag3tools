import threading
from typing import Dict, Tuple

_patched = False
_lock = threading.Lock()

# Thread-local aggregation of tokens by model
_local = threading.local()


def _get_agg() -> Dict[str, Tuple[int, int]]:
    agg = getattr(_local, "agg", None)
    if agg is None:
        agg = {}
        _local.agg = agg
    return agg


def start_capture():
    _local.prev = getattr(_local, "agg", None)
    _local.agg = {}


def stop_capture() -> Dict[str, Tuple[int, int]]:
    agg = _get_agg()
    # restore previous
    setattr(_local, "agg", getattr(_local, "prev", None))
    return agg


def ensure_openai_patched():
    global _patched
    if _patched:
        return
    with _lock:
        if _patched:
            return
        try:
            from openai.resources.chat.completions import Completions  # type: ignore
            
            # Get the original create method from the class
            _orig_create = Completions.create
            
            def _wrapped_create(self, *args, **kwargs):  # type: ignore
                resp = _orig_create(self, *args, **kwargs)
                try:
                    usage = getattr(resp, "usage", None)
                    model = kwargs.get("model") or getattr(resp, "model", None) or "unknown"
                    if usage is not None:
                        in_t = getattr(usage, "prompt_tokens", 0) or 0
                        out_t = getattr(usage, "completion_tokens", 0) or 0
                        agg = _get_agg()
                        cur_in, cur_out = agg.get(model, (0, 0))
                        agg[model] = (cur_in + in_t, cur_out + out_t)
                except Exception:
                    pass
                return resp
            
            # Replace the class method with our wrapped version
            Completions.create = _wrapped_create  # type: ignore
            _patched = True
            
        except ImportError:
            # Only set patched if we actually imported and patched OpenAI
            pass
        except Exception as e:
            # Log other errors but don't fail
            print(f"Warning: Failed to patch OpenAI completions: {e}")
