"""
Smithery MCP server integration for ag3tools.

Simple interface for discovering and using Smithery-hosted MCP servers.
All Smithery tools are automatically registered with the main ag3tools registry,
making them compatible with all LLM adapters (OpenAI, Anthropic, etc).

Usage:
    from ag3tools.tools.smithery import find, get, call

    # Find servers
    servers = find("weather")

    # Get a server (automatically registers its tools)
    weather = get("@smithery-ai/weather")
    forecast = weather.get_forecast(location="NYC")

    # Or call directly
    result = call("@smithery-ai/weather", "get_forecast", location="NYC")

    # All tools are now in the main registry and work with LLM adapters:
    from ag3tools import get_openai_tools
    tools = get_openai_tools()  # Includes all Smithery tools!
"""

# Import the core interface
from .core import (
    find,
    info,
    get,
    call,
    list_tools,
    smithery
)

# Import pre-configured tools for easy access
from .tools import context7, ddgo, exa

__all__ = [
    "find",
    "info",
    "get",
    "call",
    "list_tools",
    "smithery",
    "context7",
    "ddgo",
    "exa"
]
