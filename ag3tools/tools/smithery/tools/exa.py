"""
Exa MCP tool - Advanced AI-powered search capabilities.

Exa provides powerful semantic search for finding companies, research papers,
similar content, and specific types of information with high precision.

Usage:
    from ag3tools.tools.smithery.repertoire import exa

    # Search for companies
    companies = exa.search_companies("AI startups San Francisco")

    # Find similar content
    similar = exa.find_similar("https://example.com/article")

    # Search with specific filters
    results = exa.search("quantum computing", result_type="research")
"""

import os
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from datetime import datetime
from ..core import get, call


SERVER_NAME = "exa"  # or "@exa/exa-mcp"
_server = None


@dataclass
class ExaResult:
    """A search result from Exa."""
    title: str
    url: str
    snippet: str
    published_date: Optional[str] = None
    author: Optional[str] = None
    score: Optional[float] = None
    highlights: Optional[List[str]] = None


@dataclass
class CompanyResult:
    """A company search result from Exa."""
    name: str
    url: str
    description: str
    industry: Optional[str] = None
    location: Optional[str] = None
    founded: Optional[str] = None
    employees: Optional[str] = None
    funding: Optional[str] = None


@dataclass
class ResearchResult:
    """A research paper result from Exa."""
    title: str
    url: str
    abstract: str
    authors: Optional[List[str]] = None
    published_date: Optional[str] = None
    journal: Optional[str] = None
    citations: Optional[int] = None


def load(api_key: Optional[str] = None):
    """
    Load the Exa server and register its tools.

    Args:
        api_key: Optional Exa API key (defaults to EXA_API_KEY env var)

    Returns:
        The loaded server instance
    """
    global _server
    if _server is None:
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.getenv("EXA_API_KEY")

        config = {"apiKey": api_key} if api_key else {}

        # Try primary server name
        try:
            _server = get(SERVER_NAME, config)
        except Exception:
            # Try alternative name
            try:
                _server = get("@exa/exa-mcp", config)
            except Exception as e:
                raise RuntimeError(f"Could not load Exa server. Make sure EXA_API_KEY is set: {e}")

    return _server


def search(
    query: str,
    num_results: int = 10,
    result_type: Optional[Literal["all", "company", "research", "news"]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    **kwargs
) -> List[ExaResult]:
    """
    Perform semantic search with Exa.

    Args:
        query: Search query
        num_results: Number of results to return (default: 10)
        result_type: Filter by result type
        start_date: Filter results after this date (YYYY-MM-DD)
        end_date: Filter results before this date (YYYY-MM-DD)
        **kwargs: Additional search parameters

    Returns:
        List of ExaResult objects
    """
    load()  # Ensure server is loaded

    # Build search parameters
    params = {
        "query": query,
        "numResults": num_results
    }

    if result_type:
        params["type"] = result_type
    if start_date:
        params["startDate"] = start_date
    if end_date:
        params["endDate"] = end_date

    # Add any additional parameters
    params.update(kwargs)

    # Try different tool names that might be available
    tool_names = ["search", "exa_search", "semantic_search"]
    result = None

    for tool_name in tool_names:
        try:
            result = call(SERVER_NAME, tool_name, **params)
            break
        except Exception:
            continue

    if result is None:
        # Try with alternative server name
        for tool_name in tool_names:
            try:
                result = call("@exa/exa-mcp", tool_name, **params)
                break
            except Exception:
                continue

    # Parse results
    results = []
    if result:
        if isinstance(result, list):
            for item in result:
                if hasattr(item, 'text'):
                    # Parse text content
                    text = item.text
                    # Create basic result from text
                    results.append(ExaResult(
                        title=text[:100],
                        url="",
                        snippet=text
                    ))
                elif isinstance(item, dict):
                    results.append(ExaResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', item.get('text', '')),
                        published_date=item.get('publishedDate'),
                        author=item.get('author'),
                        score=item.get('score'),
                        highlights=item.get('highlights')
                    ))
        elif isinstance(result, dict):
            if 'results' in result:
                for r in result['results']:
                    results.append(ExaResult(
                        title=r.get('title', ''),
                        url=r.get('url', ''),
                        snippet=r.get('snippet', r.get('text', '')),
                        published_date=r.get('publishedDate'),
                        author=r.get('author'),
                        score=r.get('score'),
                        highlights=r.get('highlights')
                    ))

    return results


def search_companies(
    query: str,
    num_results: int = 10,
    location: Optional[str] = None,
    industry: Optional[str] = None,
    **kwargs
) -> List[CompanyResult]:
    """
    Search for companies using Exa.

    Args:
        query: Search query (e.g., "AI startups", "renewable energy companies")
        num_results: Number of results to return
        location: Filter by location
        industry: Filter by industry
        **kwargs: Additional search parameters

    Returns:
        List of CompanyResult objects
    """
    # Build enhanced query
    enhanced_query = query
    if location:
        enhanced_query += f" {location}"
    if industry:
        enhanced_query += f" {industry} industry"

    # Search with company-specific parameters
    results = search(
        enhanced_query,
        num_results=num_results,
        result_type="company" if "result_type" not in kwargs else kwargs.pop("result_type"),
        **kwargs
    )

    # Convert to company results
    company_results = []
    for r in results:
        company_results.append(CompanyResult(
            name=r.title,
            url=r.url,
            description=r.snippet,
            location=location,
            industry=industry
        ))

    return company_results


def find_similar(url: str, num_results: int = 10) -> List[ExaResult]:
    """
    Find content similar to the given URL.

    Args:
        url: URL of the content to find similar items for
        num_results: Number of results to return

    Returns:
        List of ExaResult objects
    """
    load()  # Ensure server is loaded

    # Try different tool names
    tool_names = ["find_similar", "similar", "findSimilar"]
    result = None

    for tool_name in tool_names:
        try:
            result = call(SERVER_NAME, tool_name, url=url, numResults=num_results)
            break
        except Exception:
            continue

    if result is None:
        # Fallback to regular search with the URL
        return search(f"similar to {url}", num_results=num_results)

    # Parse results (same as search)
    results = []
    if result:
        if isinstance(result, list):
            for item in result:
                if hasattr(item, 'text'):
                    text = item.text
                    results.append(ExaResult(
                        title=text[:100],
                        url="",
                        snippet=text
                    ))
                elif isinstance(item, dict):
                    results.append(ExaResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', item.get('text', '')),
                        published_date=item.get('publishedDate'),
                        author=item.get('author'),
                        score=item.get('score'),
                        highlights=item.get('highlights')
                    ))

    return results


def search_research(
    query: str,
    num_results: int = 10,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    **kwargs
) -> List[ResearchResult]:
    """
    Search for research papers and academic content.

    Args:
        query: Search query
        num_results: Number of results to return
        start_year: Filter papers after this year
        end_year: Filter papers before this year
        **kwargs: Additional search parameters

    Returns:
        List of ResearchResult objects
    """
    # Build date range if specified
    start_date = f"{start_year}-01-01" if start_year else None
    end_date = f"{end_year}-12-31" if end_year else None

    # Search with research-specific parameters
    results = search(
        query + " research paper academic",
        num_results=num_results,
        result_type="research" if "result_type" not in kwargs else kwargs.pop("result_type"),
        start_date=start_date,
        end_date=end_date,
        **kwargs
    )

    # Convert to research results
    research_results = []
    for r in results:
        research_results.append(ResearchResult(
            title=r.title,
            url=r.url,
            abstract=r.snippet,
            published_date=r.published_date,
            authors=[r.author] if r.author else None
        ))

    return research_results


# Convenience functions

def quick_search(query: str) -> str:
    """
    Quick search returning the first result's snippet.

    Args:
        query: Search query

    Returns:
        First result snippet or error message
    """
    results = search(query, num_results=1)
    if results:
        return results[0].snippet
    return "No results found"


def find_competitors(company_name: str, num_results: int = 5) -> List[CompanyResult]:
    """
    Find competitors of a given company.

    Args:
        company_name: Name of the company
        num_results: Number of competitors to find

    Returns:
        List of CompanyResult objects
    """
    return search_companies(
        f"competitors of {company_name} similar companies to {company_name}",
        num_results=num_results
    )


def find_trends(topic: str, num_results: int = 10) -> List[ExaResult]:
    """
    Find trending content about a topic.

    Args:
        topic: Topic to find trends for
        num_results: Number of results

    Returns:
        List of ExaResult objects
    """
    # Search for recent content
    from datetime import datetime, timedelta

    # Get content from last 30 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    return search(
        f"{topic} trends latest developments",
        num_results=num_results,
        start_date=start_date,
        end_date=end_date
    )


# Export main functions
__all__ = [
    'load',
    'search',
    'search_companies',
    'find_similar',
    'search_research',
    'quick_search',
    'find_competitors',
    'find_trends',
    'ExaResult',
    'CompanyResult',
    'ResearchResult'
]
