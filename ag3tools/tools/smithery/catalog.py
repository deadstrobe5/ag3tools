"""
Smithery catalog system for discovering available servers and tools.

This module provides discovery and search capabilities for Smithery MCP servers,
solving the problem of not knowing what's available.

Usage:
    from ag3tools.tools.smithery import catalog

    # Search for servers
    servers = catalog.search("weather")

    # Get server info
    info = catalog.get_server_info("exa")

    # List all available servers
    all_servers = catalog.list_all()

    # Get tools for a server
    tools = catalog.get_server_tools("exa")
"""

import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = Path.home() / ".ag3tools" / "smithery_cache"
CACHE_FILE = CACHE_DIR / "catalog.json"
CACHE_TTL = 86400  # 24 hours in seconds

# Known popular Smithery servers with metadata
KNOWN_SERVERS = {
    "exa": {
        "name": "exa",
        "display_name": "Exa AI Search",
        "description": "AI-powered search engine with semantic understanding",
        "category": "search",
        "requires_api_key": True,
        "api_key_env": "EXA_API_KEY",
        "api_key_url": "https://exa.ai",
        "example_tools": ["web_search_exa", "company_research_exa", "crawling_exa"],
        "example_usage": 'exa.search(query="AI breakthroughs", num_results=5)'
    },
    "@modelcontextprotocol/duckduckgo": {
        "name": "@modelcontextprotocol/duckduckgo",
        "display_name": "DuckDuckGo Search",
        "description": "Privacy-focused web search without tracking",
        "category": "search",
        "requires_api_key": False,
        "example_tools": ["search"],
        "example_usage": 'duckduckgo.search(query="Python tutorials", max_results=10)'
    },
    "@modelcontextprotocol/fetch": {
        "name": "@modelcontextprotocol/fetch",
        "display_name": "Web Fetch",
        "description": "Fetch and extract content from web pages",
        "category": "web",
        "requires_api_key": False,
        "example_tools": ["fetch"],
        "example_usage": 'fetch.fetch(url="https://example.com")'
    },
    "@modelcontextprotocol/weather": {
        "name": "@modelcontextprotocol/weather",
        "display_name": "Weather Data",
        "description": "Get weather forecasts and current conditions",
        "category": "data",
        "requires_api_key": True,
        "api_key_env": "OPENWEATHER_API_KEY",
        "api_key_url": "https://openweathermap.org/api",
        "example_tools": ["get_forecast", "get_current_weather"],
        "example_usage": 'weather.get_forecast(location="San Francisco")'
    },
    "@modelcontextprotocol/filesystem": {
        "name": "@modelcontextprotocol/filesystem",
        "display_name": "File System",
        "description": "Read, write, and manipulate files and directories",
        "category": "system",
        "requires_api_key": False,
        "example_tools": ["read_file", "write_file", "list_directory"],
        "example_usage": 'filesystem.read_file(path="/path/to/file.txt")'
    },
    "@modelcontextprotocol/github": {
        "name": "@modelcontextprotocol/github",
        "display_name": "GitHub API",
        "description": "Interact with GitHub repositories, issues, and pull requests",
        "category": "development",
        "requires_api_key": True,
        "api_key_env": "GITHUB_TOKEN",
        "api_key_url": "https://github.com/settings/tokens",
        "example_tools": ["list_repos", "create_issue", "get_pull_request"],
        "example_usage": 'github.list_repos(user="octocat")'
    },
    "@modelcontextprotocol/slack": {
        "name": "@modelcontextprotocol/slack",
        "display_name": "Slack",
        "description": "Send messages and interact with Slack workspaces",
        "category": "communication",
        "requires_api_key": True,
        "api_key_env": "SLACK_TOKEN",
        "api_key_url": "https://api.slack.com/apps",
        "example_tools": ["send_message", "list_channels"],
        "example_usage": 'slack.send_message(channel="#general", text="Hello!")'
    },
    "@modelcontextprotocol/notion": {
        "name": "@modelcontextprotocol/notion",
        "display_name": "Notion",
        "description": "Access and modify Notion databases and pages",
        "category": "productivity",
        "requires_api_key": True,
        "api_key_env": "NOTION_API_KEY",
        "api_key_url": "https://www.notion.so/my-integrations",
        "example_tools": ["query_database", "create_page", "update_page"],
        "example_usage": 'notion.query_database(database_id="...")'
    }
}


@dataclass
class ServerInfo:
    """Information about a Smithery server."""
    name: str
    display_name: str
    description: str
    category: str
    requires_api_key: bool
    api_key_env: Optional[str] = None
    api_key_url: Optional[str] = None
    example_tools: List[str] = None
    example_usage: Optional[str] = None
    last_updated: Optional[float] = None
    available: bool = True
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SmitheryCatalog:
    """Catalog of available Smithery MCP servers."""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        """Initialize the catalog."""
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "catalog.json"
        self.servers: Dict[str, ServerInfo] = {}
        self._load_known_servers()
        self._load_cache()

    def _load_known_servers(self):
        """Load the known servers into the catalog."""
        for server_id, info in KNOWN_SERVERS.items():
            self.servers[server_id] = ServerInfo(
                name=info["name"],
                display_name=info["display_name"],
                description=info["description"],
                category=info["category"],
                requires_api_key=info["requires_api_key"],
                api_key_env=info.get("api_key_env"),
                api_key_url=info.get("api_key_url"),
                example_tools=info.get("example_tools", []),
                example_usage=info.get("example_usage"),
                last_updated=time.time()
            )

    def _load_cache(self):
        """Load cached catalog from disk."""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            # Check if cache is still valid
            cache_time = cache_data.get("timestamp", 0)
            if time.time() - cache_time > CACHE_TTL:
                logger.info("Cache expired, will refresh on next fetch")
                return

            # Load additional servers from cache
            for server_id, server_data in cache_data.get("servers", {}).items():
                if server_id not in self.servers:
                    self.servers[server_id] = ServerInfo(**server_data)

            logger.info(f"Loaded {len(self.servers)} servers from cache")

        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

    def _save_cache(self):
        """Save catalog to cache."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            cache_data = {
                "timestamp": time.time(),
                "servers": {
                    server_id: server.to_dict()
                    for server_id, server in self.servers.items()
                }
            }

            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"Saved {len(self.servers)} servers to cache")

        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def search(self, query: str) -> List[ServerInfo]:
        """
        Search for servers by name, description, or category.

        Args:
            query: Search query string

        Returns:
            List of matching servers
        """
        query_lower = query.lower()
        results = []

        for server in self.servers.values():
            # Score based on matches
            score = 0

            # Check name match (highest priority)
            if query_lower in server.name.lower():
                score += 10
            if query_lower in server.display_name.lower():
                score += 8

            # Check description match
            if query_lower in server.description.lower():
                score += 5

            # Check category match
            if query_lower == server.category.lower():
                score += 7
            elif query_lower in server.category.lower():
                score += 3

            # Check tool names
            if server.example_tools:
                for tool in server.example_tools:
                    if query_lower in tool.lower():
                        score += 4
                        break

            if score > 0:
                results.append((score, server))

        # Sort by score (highest first) and return
        results.sort(key=lambda x: x[0], reverse=True)
        return [server for _, server in results]

    def get_server_info(self, server_id: str) -> Optional[ServerInfo]:
        """
        Get information about a specific server.

        Args:
            server_id: Server identifier (e.g., "exa" or "@org/name")

        Returns:
            ServerInfo or None if not found
        """
        # Try exact match first
        if server_id in self.servers:
            return self.servers[server_id]

        # Try with @ prefix if not present
        if not server_id.startswith("@"):
            prefixed = f"@modelcontextprotocol/{server_id}"
            if prefixed in self.servers:
                return self.servers[prefixed]

        # Try case-insensitive match
        for sid, server in self.servers.items():
            if sid.lower() == server_id.lower():
                return server

        return None

    def list_all(self) -> List[ServerInfo]:
        """
        List all available servers.

        Returns:
            List of all servers in the catalog
        """
        return list(self.servers.values())

    def list_by_category(self, category: str) -> List[ServerInfo]:
        """
        List servers by category.

        Args:
            category: Category name (e.g., "search", "web", "data")

        Returns:
            List of servers in the category
        """
        return [
            server for server in self.servers.values()
            if server.category.lower() == category.lower()
        ]

    def get_categories(self) -> List[str]:
        """
        Get all available categories.

        Returns:
            List of unique category names
        """
        categories = set()
        for server in self.servers.values():
            categories.add(server.category)
        return sorted(list(categories))

    def get_server_tools(self, server_id: str) -> Optional[List[str]]:
        """
        Get example tools for a server.

        Args:
            server_id: Server identifier

        Returns:
            List of tool names or None if server not found
        """
        server = self.get_server_info(server_id)
        if server:
            return server.example_tools
        return None

    def check_api_keys(self) -> Dict[str, Tuple[bool, str]]:
        """
        Check which servers have their API keys configured.

        Returns:
            Dict mapping server names to (configured, message) tuples
        """
        results = {}

        for server_id, server in self.servers.items():
            if not server.requires_api_key:
                results[server_id] = (True, "No API key required")
            elif server.api_key_env:
                if os.getenv(server.api_key_env):
                    results[server_id] = (True, f"{server.api_key_env} is set")
                else:
                    msg = f"Missing {server.api_key_env}"
                    if server.api_key_url:
                        msg += f" - Get it at: {server.api_key_url}"
                    results[server_id] = (False, msg)
            else:
                results[server_id] = (False, "API key required but env var unknown")

        return results

    def suggest_server(self, intent: str) -> Optional[ServerInfo]:
        """
        Suggest a server based on user intent.

        Args:
            intent: What the user wants to do

        Returns:
            Best matching server or None
        """
        # Keywords to category mapping
        intent_keywords = {
            "search": ["search", "find", "look up", "query", "google"],
            "web": ["fetch", "scrape", "download", "get page", "extract"],
            "data": ["weather", "forecast", "temperature", "rain"],
            "development": ["github",
