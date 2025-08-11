#!/usr/bin/env python3
"""
Simple example: find documentation URLs for popular technologies.

Usage:
  python cookbook/example_find_docs.py
"""
import ag3tools

def main():
    """Find docs for popular technologies."""
    technologies = ["fastapi", "pydantic", "langchain", "openai"]

    print("🔍 Finding documentation URLs...\n")

    for tech in technologies:
        print(f"📖 {tech}:")

        # Quick lookup
        url = ag3tools.find_docs_url(tech)
        print(f"   URL: {url}")

        # Detailed info
        result = ag3tools.invoke_tool("find_docs", technology=tech, mode="fast")
        print(f"   Reason: {result.reason}")
        print()

    # Show all available tools
    print("🛠️  Available tools:")
    tools = ag3tools.list_tools()
    for tool in tools:
        tags = f" [{', '.join(tool.tags)}]" if tool.tags else ""
        print(f"   • {tool.name}: {tool.description}{tags}")

if __name__ == "__main__":
    main()
