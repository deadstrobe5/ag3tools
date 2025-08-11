import threading
import contextvars
from typing import Dict, Tuple

_patched = False
_lock = threading.Lock()

# Context-aware aggregation of tokens by model (works with async)
_token_context: contextvars.ContextVar = contextvars.ContextVar('tokens', default={})
_prev_context: contextvars.ContextVar = contextvars.ContextVar('prev_tokens', default=None)


def _get_agg() -> Dict[str, Tuple[int, int]]:
    return _token_context.get({})


def start_capture():
    current = _token_context.get({})
    _prev_context.set(current if current else None)
    _token_context.set({})


def stop_capture() -> Dict[str, Tuple[int, int]]:
    agg = _token_context.get({})
    # restore previous
    prev = _prev_context.get(None)
    _token_context.set(prev or {})
    _prev_context.set(None)  # Clear previous context
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
