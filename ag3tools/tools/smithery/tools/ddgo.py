"""
DuckDuckGo MCP tool - Web search powered by DuckDuckGo.

Provides web search, news search, and image search capabilities through
the DuckDuckGo search engine via MCP.

Usage:
    from ag3tools.tools.smithery.repertoire import ddgo

    # Web search
    results = ddgo.search("python async programming")

    # News search
    news = ddgo.search_news("AI breakthroughs 2024")

    # Image search
    images = ddgo.search_images("beautiful landscapes")
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from ..core import get, call


SERVER_NAME = "@modelcontextprotocol/ddg"
_server = None


@dataclass
class SearchResult:
    """A search result from DuckDuckGo."""
    title: str
    url: str
    snippet: str
    source: Optional[str] = None


@dataclass
class NewsResult:
    """A news result from DuckDuckGo."""
    title: str
    url: str
    excerpt: str
    date: Optional[str] = None
    source: Optional[str] = None


@dataclass
class ImageResult:
    """An image result from DuckDuckGo."""
    title: str
    url: str
    thumbnail: str
    source: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


def load():
    """
    Load the DuckDuckGo server and register its tools.

    Returns:
        The loaded server instance
    """
    global _server
    if _server is None:
        _server = get(SERVER_NAME)
    return _server


def search(query: str, max_results: int = 10) -> List[SearchResult]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query
        max_results: Maximum number of results (default: 10)

    Returns:
        List of SearchResult objects
    """
    load()  # Ensure server is loaded

    result = call(
        SERVER_NAME,
        "search",
        query=query,
        max_results=max_results
    )

    # Parse results
    results = []
    if result:
        # Handle different response formats
        if isinstance(result, list):
            for item in result:
                if hasattr(item, 'text'):
                    # Parse text content
                    text = item.text
                    # Simple parsing - this may need adjustment based on actual format
                    lines = text.split('\n')
                    for line in lines:
                        if line.strip():
                            # Create a basic result
                            results.append(SearchResult(
                                title=line[:100],  # First 100 chars as title
                                url="",
                                snippet=line
                            ))
                elif isinstance(item, dict):
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', ''),
                        source=item.get('source')
                    ))
        elif isinstance(result, dict):
            if 'results' in result:
                for r in result['results']:
                    results.append(SearchResult(
                        title=r.get('title', ''),
                        url=r.get('url', ''),
                        snippet=r.get('snippet', ''),
                        source=r.get('source')
                    ))

    return results


def search_news(query: str, max_results: int = 10) -> List[NewsResult]:
    """
    Search news using DuckDuckGo.

    Args:
        query: Search query
        max_results: Maximum number of results (default: 10)

    Returns:
        List of NewsResult objects
    """
    load()  # Ensure server is loaded

    result = call(
        SERVER_NAME,
        "news",
        query=query,
        max_results=max_results
    )

    # Parse results
    news_results = []
    if result:
        # Handle different response formats
        if isinstance(result, list):
            for item in result:
                if hasattr(item, 'text'):
                    # Parse text content
                    text = item.text
                    lines = text.split('\n')
                    for line in lines:
                        if line.strip():
                            news_results.append(NewsResult(
                                title=line[:100],
                                url="",
                                excerpt=line
                            ))
                elif isinstance(item, dict):
                    news_results.append(NewsResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        excerpt=item.get('excerpt', ''),
                        date=item.get('date'),
                        source=item.get('source')
                    ))
        elif isinstance(result, dict):
            if 'results' in result:
                for r in result['results']:
                    news_results.append(NewsResult(
                        title=r.get('title', ''),
                        url=r.get('url', ''),
                        excerpt=r.get('excerpt', ''),
                        date=r.get('date'),
                        source=r.get('source')
                    ))

    return news_results


def search_images(query: str, max_results: int = 10) -> List[ImageResult]:
    """
    Search images using DuckDuckGo.

    Args:
        query: Search query
        max_results: Maximum number of results (default: 10)

    Returns:
        List of ImageResult objects
    """
    load()  # Ensure server is loaded

    result = call(
        SERVER_NAME,
        "images",
        query=query,
        max_results=max_results
    )

    # Parse results
    image_results = []
    if result:
        # Handle different response formats
        if isinstance(result, list):
            for item in result:
                if hasattr(item, 'text'):
                    # Parse text content
                    text = item.text
                    lines = text.split('\n')
                    for line in lines:
                        if line.strip():
                            image_results.append(ImageResult(
                                title=line[:100],
                                url="",
                                thumbnail=""
                            ))
                elif isinstance(item, dict):
                    image_results.append(ImageResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        thumbnail=item.get('thumbnail', ''),
                        source=item.get('source'),
                        width=item.get('width'),
                        height=item.get('height')
                    ))
        elif isinstance(result, dict):
            if 'results' in result:
                for r in result['results']:
                    image_results.append(ImageResult(
                        title=r.get('title', ''),
                        url=r.get('url', ''),
                        thumbnail=r.get('thumbnail', ''),
                        source=r.get('source'),
                        width=r.get('width'),
                        height=r.get('height')
                    ))

    return image_results


# Convenience functions for common searches

def quick_search(query: str) -> str:
    """
    Quick web search returning just the first result's snippet.

    Args:
        query: Search query

    Returns:
        First result snippet or error message
    """
    results = search(query, max_results=1)
    if results:
        return results[0].snippet
    return "No results found"


def get_latest_news(topic: str, count: int = 5) -> List[str]:
    """
    Get latest news headlines about a topic.

    Args:
        topic: Topic to search for
        count: Number of headlines to return

    Returns:
        List of news headlines
    """
    news = search_news(topic, max_results=count)
    return [n.title for n in news]


def find_definition(term: str) -> str:
    """
    Find the definition of a term.

    Args:
        term: Term to define

    Returns:
        Definition or "No definition found"
    """
    results = search(f"define {term}", max_results=3)
    if results:
        # Look for a result that seems like a definition
        for r in results:
            if "definition" in r.snippet.lower() or "meaning" in r.snippet.lower():
                return r.snippet
        # Return first result if no obvious definition
        return results[0].snippet
    return "No definition found"


# Export main functions
__all__ = [
    'load',
    'search',
    'search_news',
    'search_images',
    'quick_search',
    'get_latest_news',
    'find_definition',
    'SearchResult',
    'NewsResult',
    'ImageResult'
]
