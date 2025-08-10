from typing import List

try:
    from ddgs import DDGS  # type: ignore
except Exception:  # pragma: no cover
    from duckduckgo_search import DDGS  # type: ignore

from ag3tools.core.types import WebSearchInput, SearchResult
from ag3tools.core.registry import register_tool
import asyncio
from ag3tools.core.cache import cache_get, cache_set


@register_tool(
    description="Web search using DuckDuckGo (ddgs). Returns a list of normalized search results.",
    input_model=WebSearchInput,
    tags=["search"],
)
def web_search(input: WebSearchInput) -> List[SearchResult]:
    cached = cache_get("web_search", input.query, input.max_results)
    if cached is not None:
        return cached
    with DDGS() as ddg:
        results = ddg.text(
            input.query,
            max_results=input.max_results,
            safesearch="moderate",
            region="wt-wt",
        ) or []
    cleaned = [
        SearchResult(
            title=r.get("title", "") or "",
            url=r.get("href", "") or r.get("url", "") or "",
            snippet=r.get("body", "") or "",
        )
        for r in results
    ]
    cache_set("web_search", cleaned, input.query, input.max_results)
    return cleaned


@register_tool(
    description="Async variant of web_search (runs provider in a worker thread).",
    input_model=WebSearchInput,
    tags=["search", "async"],
)
async def web_search_async(input: WebSearchInput) -> List[SearchResult]:
    return await asyncio.to_thread(web_search, input)