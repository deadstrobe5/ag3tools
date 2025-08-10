"""agtools public API.

Auto-loads all tools recursively from ag3tools.tools.* so you never update exports.
"""

# Auto-import all types and registry functions
from .core.types import *  # noqa: F401,F403
from .core.registry import *  # noqa: F401,F403

# Auto-import all tools by recursively scanning tools/ directory
import importlib
import pkgutil
from pathlib import Path

_tools_dir = Path(__file__).parent / "tools"
_pkg_prefix = f"{__package__}.tools."

for mod in pkgutil.walk_packages([str(_tools_dir)], prefix=_pkg_prefix):
    fullname = mod.name
    try:
        importlib.import_module(fullname)
    except Exception:
        # Keep import failures non-fatal; tools should be robust to optional deps
        continue

# Import adapter helpers
from .adapters.openai_tools import (
    openai_tool_specs_from_registry,
    run_openai_tool_call_from_registry,
)
from .adapters.langchain_tools import langchain_tools_from_registry

# Convenience functions
def find_docs_url(technology: str) -> str | None:
    """Convenience: return only the URL or None."""
    return invoke_tool("find_docs", technology=technology).url


