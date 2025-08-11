"""ag3tools public API.

Simple, clean interface that exposes only the core registry functions.
"""

# Import and auto-load all tools
import importlib
import pkgutil
from pathlib import Path

# Core registry functions - this is the main API
from .core.registry import (
    invoke_tool,
    list_tools,
    get_tool_spec,
    invoke_tool_async,
    register_tool,
    tool_summaries,
    ToolSpec,
)

# Explicitly define public API
__all__ = [
    "invoke_tool",
    "list_tools",
    "get_tool_spec",
    "invoke_tool_async",
    "register_tool",
    "tool_summaries",
    "ToolSpec",
    "find_docs_url",
    "get_openai_tools",
    "get_langchain_tools",
    "run_openai_tool_call",
]

# Auto-load all tools by scanning tools/ directory
# This registers them with the registry
_tools_dir = Path(__file__).parent / "tools"
_pkg_prefix = f"{__package__}.tools."

for mod in pkgutil.walk_packages([str(_tools_dir)], prefix=_pkg_prefix):
    try:
        importlib.import_module(mod.name)
    except Exception:
        # Keep import failures non-fatal
        continue

# Convenience function
def find_docs_url(technology: str) -> str | None:
    """Quick way to get just the docs URL."""
    result = invoke_tool("find_docs", technology=technology)
    return result.url if hasattr(result, 'url') else None

# Optional adapter functions (lazy loaded)
def get_openai_tools():
    """Get OpenAI function specs for all tools."""
    try:
        from .adapters.openai_tools import openai_tool_specs_from_registry
        return openai_tool_specs_from_registry()
    except ImportError:
        raise ImportError("OpenAI adapter requires: pip install openai")

def get_langchain_tools():
    """Get LangChain tools for all tools."""
    try:
        from .adapters.langchain_tools import langchain_tools_from_registry
        return langchain_tools_from_registry()
    except ImportError:
        raise ImportError("LangChain adapter requires: pip install langchain")

def run_openai_tool_call(tool_call):
    """Execute an OpenAI tool call."""
    try:
        from .adapters.openai_tools import run_openai_tool_call_from_registry
        return run_openai_tool_call_from_registry(tool_call)
    except ImportError:
        raise ImportError("OpenAI adapter requires: pip install openai")
