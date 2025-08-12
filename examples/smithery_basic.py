#!/usr/bin/env python3
"""
Simple Smithery MCP server usage example.

This shows the easiest way to find and use Smithery servers with ag3tools.
"""

import os
from ag3tools import smithery


def main():
    """Demonstrate Smithery usage."""

    print("=" * 60)
    print("SMITHERY MCP SERVERS - SIMPLE EXAMPLE")
    print("=" * 60)

    # 1. Find servers by topic
    print("\n1. FINDING SERVERS")
    print("-" * 40)
    try:
        servers = smithery.find("weather", limit=5)
        print(f"Found {len(servers)} weather servers:")
        for server in servers[:3]:
            print(f"  • {server['name']}: {server['description'][:50]}...")
    except Exception as e:
        print(f"Search failed: {e}")
        print("Make sure SMITHERY_API_KEY is set in your .env file")

    # 2. Get server info
    print("\n2. SERVER INFO")
    print("-" * 40)
    try:
        info = smithery.info("@smithery-ai/national-weather-service")
        if info:
            print(f"Server: {info.display_name}")
            print(f"Tools: {len(info.tools)} available")
            for tool in info.tools[:3]:
                print(f"  • {tool['name']}: {tool['description'][:40]}...")
    except Exception as e:
        print(f"Info failed: {e}")

    # 3. Use a server
    print("\n3. USING A SERVER")
    print("-" * 40)
    try:
        # Get a server instance
        weather = smithery.get("@smithery-ai/national-weather-service")
        print(f"Loaded server with tools: {weather.list_tools()}")

        # Call a tool (example - would need valid coordinates)
        # forecast = weather.get_weather_forecast(location="40.7,-74.0")
        # print(f"Forecast: {forecast}")
        print("(Tool execution skipped in example)")

    except Exception as e:
        print(f"Server usage failed: {e}")

    # 4. Direct tool call
    print("\n4. DIRECT TOOL CALL")
    print("-" * 40)
    try:
        # Call a tool directly without getting the server first
        # result = smithery.call("@smithery-ai/national-weather-service",
        #                       "get_current_weather",
        #                       location="40.7,-74.0")
        print("Direct call syntax:")
        print('  smithery.call("server-name", "tool-name", **params)')

    except Exception as e:
        print(f"Direct call failed: {e}")

    # 5. Common patterns
    print("\n5. COMMON PATTERNS")
    print("-" * 40)
    print("""
# Find servers by topic
servers = smithery.find("search")  # Find search servers
servers = smithery.find("memory")  # Find memory/storage servers

# Get and use a server
server = smithery.get("server-name")
result = server.tool_name(param="value")

# Direct call
result = smithery.call("server-name", "tool-name", param="value")

# Dictionary/attribute access
result = smithery["server-name"].tool_name(param="value")
""")

    print("\n" + "=" * 60)
    print("SETUP REQUIREMENTS")
    print("=" * 60)
    print("""
1. Set SMITHERY_API_KEY in your .env file
   Get your key at: https://smithery.ai

2. Set any server-specific API keys:
   - EXA_API_KEY for Exa search
   - OPENWEATHER_API_KEY for weather servers
   - etc.

3. Install required packages:
   pip install httpx mcp python-dotenv

That's it! The new simplified interface handles everything else.
""")


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("SMITHERY_API_KEY"):
        print("⚠️  SMITHERY_API_KEY not found in environment")
        print("   Please set it in your .env file")
        print("   Get your key at: https://smithery.ai\n")

    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
