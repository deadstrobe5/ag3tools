from typing import List

try:
    from ddgs import DDGS  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from duckduckgo_search import DDGS  # type: ignore
    except ImportError:
        raise ImportError("Please install ddgs: pip install ddgs")

from pydantic import BaseModel, Field
from ag3tools.core.registry import register_tool
from ag3tools.core.types import ToolResult
import asyncio
from ag3tools.core.cache import cache_get, cache_set


class WebSearchInput(BaseModel):
    query: str
    max_results: int = 12


class SearchResult(BaseModel):
    title: str = Field(default="")
    url: str = Field(default="")
    snippet: str = Field(default="")


class WebSearchOutput(ToolResult):
    results: List[SearchResult] = []


@register_tool(
    description="Web search using DuckDuckGo (ddgs). Returns a list of normalized search results.",
    input_model=WebSearchInput,
    output_model=WebSearchOutput,
    tags=["search"],
)
def web_search(input: WebSearchInput) -> WebSearchOutput:
    cached = cache_get("web_search", input.query, input.max_results)
    if cached is not None:
        return WebSearchOutput(results=cached)

    try:
        with DDGS() as ddg:
            results = ddg.text(
                input.query,
                max_results=input.max_results,
                safesearch="moderate",
                region="wt-wt",
            ) or []
    except Exception as e:
        return WebSearchOutput(
            success=False,
            error_message=f"Search failed: {str(e)}",
            error_code="SEARCH_ERROR"
        )

    cleaned = [
        SearchResult(
            title=r.get("title", "") or "",
            url=r.get("href", "") or r.get("url", "") or "",
            snippet=r.get("body", "") or "",
        )
        for r in results
    ]
    cache_set("web_search", cleaned, input.query, input.max_results)
    return WebSearchOutput(results=cleaned)


@register_tool(
    description="Async variant of web_search (runs provider in a worker thread).",
    input_model=WebSearchInput,
    output_model=WebSearchOutput,
    tags=["search", "async"],
)
async def web_search_async(input: WebSearchInput) -> WebSearchOutput:
    return await asyncio.to_thread(web_search, input)
