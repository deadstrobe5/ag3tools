"""
Pre-configured Smithery tools for easy access.

These are commonly used Smithery MCP servers with simplified interfaces.

Usage:
    from ag3tools import smithery

    # Use Context7 for documentation
    docs = smithery.context7.get_react_docs("hooks")

    # Search with DuckDuckGo
    results = smithery.ddgo.search("python async programming")

    # Use Exa for advanced search
    companies = smithery.exa.find_companies("AI startups San Francisco")
"""

# Import individual tool modules
from . import context7
from . import ddgo
from . import exa

# Optional: Import commonly used functions directly
from .context7 import get_docs, find_library
from .ddgo import search, search_news
from .exa import find_similar, search_companies

# Available pre-configured tools
AVAILABLE_TOOLS = {
    "context7": "Documentation and code examples for libraries",
    "ddgo": "DuckDuckGo web search",
    "exa": "Advanced AI-powered search"
}

__all__ = [
    # Modules
    "context7",
    "ddgo",
    "exa",

    # Direct functions
    "get_docs",
    "find_library",
    "search",
    "search_news",
    "find_similar",
    "search_companies",

    # Info
    "AVAILABLE_TOOLS",
    "load_all"
]


def load_all():
    """
    Load all pre-configured tools at once.

    This ensures all tools are registered with the main ag3tools registry
    and ready for use with LLM adapters.

    Returns:
        dict: Mapping of tool names to their loaded servers
    """
    servers = {}

    # Load each tool
    servers["context7"] = context7.load()
    servers["ddgo"] = ddgo.load()
    servers["exa"] = exa.load()

    return servers
