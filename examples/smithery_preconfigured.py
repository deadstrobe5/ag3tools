#!/usr/bin/env python3
"""
Example demonstrating the simplified Smithery tools interface.

Access pre-configured Smithery tools directly through the smithery module.
No need to worry about repertoires or complex imports.
"""

import os
from ag3tools import smithery


def demo_context7():
    """Demonstrate Context7 for documentation."""
    print("\n" + "="*60)
    print("Context7 - Documentation Tool")
    print("="*60)

    # Find React libraries
    print("\nFinding React libraries...")
    libs = smithery.context7.find_library("react")

    print(f"Found {len(libs)} React libraries. Top 3:")
    for lib in libs[:3]:
        print(f"  • {lib.title} (Trust: {lib.trust_score})")
        print(f"    ID: {lib.id}")
        print(f"    Snippets: {lib.snippets}")

    # Get React hooks documentation
    print("\nGetting React hooks documentation...")
    docs = smithery.context7.get_react_docs("useState useEffect", tokens=500)
    print("\nReact Hooks Docs (first 400 chars):")
    print("-" * 40)
    print(docs[:400])
    if len(docs) > 400:
        print("... (truncated)")


def demo_ddgo():
    """Demonstrate DuckDuckGo search."""
    print("\n" + "="*60)
    print("DuckDuckGo - Web Search")
    print("="*60)

    # Quick search
    print("\nSearching for 'Python async programming'...")
    results = smithery.ddgo.search("Python async programming", max_results=3)

    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Snippet: {result.snippet[:150]}...")

    # Get latest news
    print("\n\nGetting latest AI news...")
    news = smithery.ddgo.get_latest_news("artificial intelligence", count=3)
    print("Latest headlines:")
    for headline in news:
        print(f"  • {headline}")


def demo_exa():
    """Demonstrate Exa advanced search."""
    print("\n" + "="*60)
    print("Exa - Advanced AI Search")
    print("="*60)

    # Note: Exa requires an API key
    if not os.getenv("EXA_API_KEY"):
        print("\n⚠️  Exa requires EXA_API_KEY environment variable")
        print("   Skipping Exa demo...")
        return

    # Search for companies
    print("\nSearching for AI startups...")
    companies = smithery.exa.search_companies("AI startups San Francisco", num_results=3)

    print(f"\nFound {len(companies)} companies:")
    for company in companies:
        print(f"  • {company.name}")
        print(f"    {company.description[:100]}...")

    # Find trending topics
    print("\n\nFinding trends in quantum computing...")
    trends = smithery.exa.find_trends("quantum computing", num_results=3)

    print(f"Latest trends:")
    for trend in trends:
        print(f"  • {trend.title}")
        print(f"    {trend.snippet[:100]}...")


def main():
    """Run all demos."""

    # Set up environment if needed
    if not os.getenv("SMITHERY_API_KEY"):
        os.environ["SMITHERY_API_KEY"] = "0fe98d0c-7831-4c46-9c51-a8f3dfd8bd3c"

    print("\n" + "="*60)
    print("Smithery Tools Demo")
    print("Simple access to powerful MCP tools")
    print("="*60)

    # The beauty of the new interface - just use smithery.tool_name!
    print("""
How to use:
    from ag3tools import smithery

    # Context7 for documentation
    docs = smithery.context7.get_react_docs("hooks")

    # DuckDuckGo for search
    results = smithery.ddgo.search("python tutorials")

    # Exa for advanced search (requires API key)
    companies = smithery.exa.find_companies("AI startups")
""")

    # Run demos
    try:
        demo_context7()
    except Exception as e:
        print(f"\nContext7 error: {e}")

    try:
        demo_ddgo()
    except Exception as e:
        print(f"\nDuckDuckGo error: {e}")

    try:
        demo_exa()
    except Exception as e:
        print(f"\nExa error: {e}")

    # Show registry integration
    print("\n" + "="*60)
    print("Registry Integration")
    print("="*60)

    from ag3tools import list_tools

    all_tools = list_tools()
    smithery_tools = [t for t in all_tools if t.name.startswith("smithery:")]

    print(f"\n✓ All {len(smithery_tools)} Smithery tools are registered:")
    unique_servers = set()
    for tool in smithery_tools:
        parts = tool.name.split(":")
        if len(parts) >= 2:
            unique_servers.add(parts[1])

    print(f"  From {len(unique_servers)} different servers:")
    for server in sorted(unique_servers):
        print(f"    • {server}")

    print("\n" + "="*60)
    print("✓ Demo Complete!")
    print("="*60)
    print("""
The simplified interface makes it easy:
- No complex imports
- Just use smithery.tool_name
- All tools auto-register with ag3tools
- Ready for use with any LLM adapter
""")


if __name__ == "__main__":
    main()
