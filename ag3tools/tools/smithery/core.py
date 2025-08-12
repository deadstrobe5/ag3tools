"""
Simplified Smithery MCP server integration.

This single module handles everything you need for Smithery servers:
- Discovery: Find servers by topic or tool
- Import: Load any server with zero config
- Execute: Call tools directly

Usage:
    from ag3tools.tools.smithery import simple as smithery

    # Find servers
    servers = smithery.find("weather")

    # Use a server
    result = smithery.call("@smithery-ai/weather", "get_forecast", location="NYC")

    # Or get a server object
    weather = smithery.get("@smithery-ai/weather")
    forecast = weather.get_forecast(location="NYC")
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import BaseModel, Field, create_model

# Import the main registry for tool registration
from ag3tools.core.registry import register_tool

logger = logging.getLogger(__name__)

# Global state
_servers = {}  # Cache of imported servers
_registry_cache = {}  # Cache of registry data


@dataclass
class ServerInfo:
    """Basic server information."""
    name: str
    display_name: str
    description: str
    tools: List[Dict[str, Any]]
    remote: bool = True


class SmitheryServer:
    """Simple wrapper for a Smithery MCP server."""

    def __init__(self, name: str, client_url: str, config: Optional[Dict] = None):
        self.name = name
        self.url = client_url
        self.config = config or {}
        self.tools = {}
        self._initialized = False

    async def _init(self):
        """Initialize connection and discover tools."""
        if self._initialized:
            return

        try:
            async with streamablehttp_client(self.url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    # Get available tools
                    tools_response = await session.list_tools()
                    for tool in tools_response.tools:
                        self.tools[tool.name] = tool
                        # Create a method for each tool
                        setattr(self, tool.name, self._make_tool_wrapper(tool.name))

                        # Register with the main ag3tools registry
                        self._register_tool_with_registry(tool)

                    self._initialized = True
                    logger.info(f"Initialized {self.name} with {len(self.tools)} tools")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize {self.name}: {e}")

    def _register_tool_with_registry(self, tool):
        """Register a Smithery tool with the main ag3tools registry."""
        # Create input model from tool schema
        input_fields = {}

        if hasattr(tool, 'inputSchema') and tool.inputSchema:
            schema = tool.inputSchema
            if 'properties' in schema:
                for field_name, field_schema in schema['properties'].items():
                    field_type = str  # Default type

                    # Map JSON schema types to Python types
                    if 'type' in field_schema:
                        type_map = {
                            'string': str,
                            'number': float,
                            'integer': int,
                            'boolean': bool,
                            'array': list,
                            'object': dict
                        }
                        field_type = type_map.get(field_schema['type'], str)

                    # Check if required
                    is_required = field_name in schema.get('required', [])

                    # Create field with description
                    field_description = field_schema.get('description', '')
                    default = ... if is_required else field_schema.get('default', None)

                    input_fields[field_name] = (field_type, Field(default, description=field_description))

        # Create dynamic input model
        if input_fields:
            InputModel = create_model(
                f"{self.name}_{tool.name}_Input",
                **input_fields,
                __base__=BaseModel
            )
        else:
            # No inputs needed - create empty model
            InputModel = create_model(
                f"{self.name}_{tool.name}_Input",
                __base__=BaseModel
            )

        # Create the tool function
        def tool_function(input_data: BaseModel):
            """Execute Smithery tool through MCP."""
            # Convert input model to dict
            kwargs = input_data.dict() if hasattr(input_data, 'dict') else {}

            # Execute through the server's wrapper
            return self._execute_tool_sync(tool.name, **kwargs)

        # Register with the main registry
        full_tool_name = f"smithery:{self.name}:{tool.name}"
        description = getattr(tool, 'description', f"Smithery tool {tool.name}")

        register_tool(
            name=full_tool_name,
            description=description,
            input_model=InputModel,
            tags=["smithery", "mcp", self.name]
        )(tool_function)

        logger.debug(f"Registered tool {full_tool_name} with main registry")

    def _execute_tool_sync(self, tool_name: str, **kwargs):
        """Execute a tool synchronously for registry compatibility."""
        async def async_exec():
            if not self._initialized:
                await self._init()

            async with streamablehttp_client(self.url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, kwargs)
                    return result.content if hasattr(result, 'content') else result

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create a new event loop in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, async_exec())
                    return future.result()
            return loop.run_until_complete(async_exec())
        except RuntimeError:
            return asyncio.run(async_exec())

    def _make_tool_wrapper(self, tool_name: str):
        """Create a wrapper function for a tool."""
        def sync_call(**kwargs):
            """Synchronous wrapper."""
            return self._execute_tool_sync(tool_name, **kwargs)

        return sync_call

    def list_tools(self) -> List[str]:
        """List available tool names."""
        return list(self.tools.keys())

    def __repr__(self):
        return f"<SmitheryServer '{self.name}' with {len(self.tools)} tools>"


class SimpleSmithery:
    """Simple all-in-one Smithery interface."""

    def __init__(self):
        self.api_key = None
        self._ensure_env()
        # Pre-configured tool attributes (will be set later)
        from types import ModuleType
        self.context7: Optional[ModuleType] = None
        self.ddgo: Optional[ModuleType] = None
        self.exa: Optional[ModuleType] = None

    def _ensure_env(self):
        """Load environment variables."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        self.api_key = os.getenv("SMITHERY_API_KEY")
        if not self.api_key:
            logger.warning("SMITHERY_API_KEY not found. Discovery features will be limited.")

    def find(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find servers by search query.

        Args:
            query: Search term (e.g., "weather", "search", "memory")
            limit: Maximum results to return

        Returns:
            List of server info dicts with name, description, and tools
        """
        if not self.api_key:
            raise ValueError("SMITHERY_API_KEY required for discovery. Set it in your .env file.")

        # Check cache first
        cache_key = f"search:{query}:{limit}"
        if cache_key in _registry_cache:
            return _registry_cache[cache_key]

        try:
            with httpx.Client() as client:
                response = client.get(
                    "https://registry.smithery.ai/servers",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"q": query, "pageSize": str(limit)}
                )
                response.raise_for_status()
                data = response.json()

                results = []
                for server in data["servers"]:
                    results.append({
                        "name": server["qualifiedName"],
                        "display_name": server.get("displayName", server["qualifiedName"]),
                        "description": server.get("description", ""),
                        "use_count": server.get("useCount", 0)
                    })

                _registry_cache[cache_key] = results
                return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def info(self, server_name: str) -> Optional[ServerInfo]:
        """
        Get detailed information about a server.

        Args:
            server_name: Full server name (e.g., "@smithery-ai/weather")

        Returns:
            ServerInfo object or None if not found
        """
        if not self.api_key:
            return None

        # Check cache
        if server_name in _registry_cache:
            return _registry_cache[server_name]

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://registry.smithery.ai/servers/{server_name}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()

                info = ServerInfo(
                    name=data["qualifiedName"],
                    display_name=data.get("displayName", data["qualifiedName"]),
                    description=data.get("description", ""),
                    tools=data.get("tools", []),
                    remote=data.get("remote", True)
                )

                _registry_cache[server_name] = info
                return info

        except Exception as e:
            logger.error(f"Failed to get info for {server_name}: {e}")
            return None

    def get(self, server_name: str, config: Optional[Dict] = None) -> SmitheryServer:
        """
        Get or import a Smithery server.

        Args:
            server_name: Server name (e.g., "exa" or "@smithery-ai/weather")
            config: Optional configuration dict (e.g., {"apiKey": "..."})

        Returns:
            SmitheryServer object ready to use
        """
        # Check cache
        cache_key = f"{server_name}:{hash(frozenset(config.items())) if config else 0}"
        if cache_key in _servers:
            return _servers[cache_key]

        # Auto-configure known servers
        if not config:
            config = self._auto_config(server_name)

        # Build Smithery URL
        url = self._build_url(server_name, config)

        # Create server wrapper
        server = SmitheryServer(server_name, url, config)

        # Initialize it (this loads and registers the tools)
        try:
            asyncio.run(server._init())
        except RuntimeError:
            # Already in async context or no loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Can't use run_until_complete in running loop
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, server._init())
                        future.result()
                else:
                    loop.run_until_complete(server._init())
            except RuntimeError:
                # No loop at all, create one
                asyncio.run(server._init())

        _servers[cache_key] = server
        return server

    def call(self, server_name: str, tool_name: str, **kwargs) -> Any:
        """
        Call a tool directly without getting the server object.

        Args:
            server_name: Server name
            tool_name: Tool name
            **kwargs: Tool arguments

        Returns:
            Tool result

        Example:
            >>> result = smithery.call("@smithery-ai/weather", "get_forecast", location="NYC")
        """
        server = self.get(server_name)

        if not hasattr(server, tool_name):
            available = server.list_tools()
            raise AttributeError(
                f"Tool '{tool_name}' not found in {server_name}. "
                f"Available tools: {', '.join(available)}"
            )

        tool_func = getattr(server, tool_name)
        return tool_func(**kwargs)

    def list_tools(self, server_name: str) -> List[str]:
        """List tools available in a server."""
        server = self.get(server_name)
        return server.list_tools()

    def _auto_config(self, server_name: str) -> Dict[str, Any]:
        """Auto-configure known servers from environment."""
        config = {}

        # Known server configurations
        if "exa" in server_name.lower():
            exa_key = os.getenv("EXA_API_KEY")
            if exa_key:
                config["exaApiKey"] = exa_key
        elif "weather" in server_name.lower():
            weather_key = os.getenv("OPENWEATHER_API_KEY")
            if weather_key:
                config["openweathermap_api_key"] = weather_key

        return config

    def _build_url(self, server_name: str, config: Dict[str, Any]) -> str:
        """Build the Smithery server URL."""
        if not self.api_key:
            raise ValueError("SMITHERY_API_KEY required. Set it in your .env file.")

        # Base URL
        base_url = f"https://server.smithery.ai/{server_name}/mcp"

        # Add API key
        params = [f"api_key={self.api_key}"]

        # Add config as query params
        for key, value in config.items():
            params.append(f"{key}={value}")

        return f"{base_url}?{'&'.join(params)}"

    def __getattr__(self, name: str):
        """Allow attribute access to servers."""
        # Don't auto-initialize at import time
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        # Return a lazy wrapper that will initialize on first use
        class LazyServer:
            def __init__(self, smithery, server_name):
                self._smithery = smithery
                self._server_name = server_name
                self._server = None

            def __getattr__(self, tool_name):
                if self._server is None:
                    self._server = self._smithery.get(self._server_name)
                return getattr(self._server, tool_name)

            def __call__(self, *args, **kwargs):
                if self._server is None:
                    self._server = self._smithery.get(self._server_name)
                return self._server(*args, **kwargs)

        return LazyServer(self, name)

    def __getitem__(self, name: str):
        """Allow dictionary access to servers."""
        # Don't auto-initialize at import time
        return self.__getattr__(name)


# Create singleton instance
_instance = SimpleSmithery()

# Export convenient functions
find = _instance.find
info = _instance.info
get = _instance.get
call = _instance.call
list_tools = _instance.list_tools

# Also allow using the instance directly
smithery = _instance

# Add convenient access to pre-configured tools
from . import tools as _tools
smithery.context7 = _tools.context7
smithery.ddgo = _tools.ddgo
smithery.exa = _tools.exa

def load_servers(*server_names):
    """
    Load multiple Smithery servers at once, registering all their tools.

    Args:
        *server_names: Server names to load

    Returns:
        Dict mapping server names to server instances

    Example:
        >>> servers = load_servers(
        ...     "@smithery-ai/weather",
        ...     "exa",
        ...     "@modelcontextprotocol/fetch"
        ... )
        >>> # All tools from these servers are now in the main registry
    """
    servers = {}
    for name in server_names:
        try:
            servers[name] = get(name)
        except Exception as e:
            print(f"Warning: Could not load {name}: {e}")
    return servers

def load_by_capability(*capabilities):
    """
    Discover and load servers by capability, registering all their tools.

    Args:
        *capabilities: Capabilities to search for (e.g., "search", "weather")

    Returns:
        Dict mapping server names to server instances

    Example:
        >>> # Load all servers that can do search and weather
        >>> servers = load_by_capability("search", "weather")
        >>>
        >>> # Now use with LLMs through the main registry
        >>> from ag3tools import get_openai_tools
        >>> tools = get_openai_tools()  # Includes all loaded tools
    """
    discovered_servers = set()

    for capability in capabilities:
        found = find(capability, limit=10)
        for server_info in found:
            discovered_servers.add(server_info['name'])

    # Load all discovered servers
    servers = {}
    for server_name in discovered_servers:
        try:
            servers[server_name] = get(server_name)
        except Exception as e:
            print(f"Warning: Could not load {server_name}: {e}")

    return servers

# Don't replace the module - keep normal Python module behavior
# This avoids initialization issues at import time
__all__ = ['find', 'info', 'get', 'call', 'list_tools', 'smithery', 'load_servers', 'load_by_capability', 'SimpleSmithery', 'SmitheryServer', 'ServerInfo', 'context7', 'ddgo', 'exa']

# Export pre-configured tools for direct access
from .tools import context7, ddgo, exa
