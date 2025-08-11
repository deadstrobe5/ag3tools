from typing import Optional, Literal
from pydantic import BaseModel
from ag3tools.tools.search.web_search import web_search, WebSearchInput
from ag3tools.tools.docs.rank_docs import rank_docs, RankDocsInput
from ag3tools.tools.docs.rank_docs_llm import rank_docs_llm, RankDocsLLMInput
from ag3tools.tools.net.fetch_page import fetch_page, FetchPageInput
from ag3tools.tools.docs.validate_docs_llm import validate_docs_llm, ValidateDocsLLMInput
from ag3tools.core.registry import register_tool


class FindDocsInput(BaseModel):
    technology: str
    mode: Literal["fast", "validated", "cracked"] = "fast"
    top_k: int = 6
    llm_model: str = "gpt-4o-mini"


class FindDocsOutput(BaseModel):
    url: Optional[str]
    title: Optional[str] = None
    reason: Optional[str] = None


@register_tool(
    description="Find the official documentation URL for a technology by composing search + ranking.",
    input_model=FindDocsInput,
    tags=["docs"],
)
def find_docs(input: FindDocsInput) -> FindDocsOutput:
    """Return the top documentation URL for a technology.

    Strategy: run a few short queries, merge results, rank heuristically.
    """
    queries = [
        f"{input.technology} official documentation",
        f"{input.technology} docs",
        f"{input.technology} api reference",
    ]
    results = []
    for q in queries:
        results.extend(web_search(WebSearchInput(query=q, max_results=input.top_k)))
    ranked = rank_docs(RankDocsInput(technology=input.technology, candidates=results))
    if not ranked:
        return FindDocsOutput(url=None, reason="no_results")

    if input.mode == "fast":
        top = ranked[0]
        return FindDocsOutput(url=top.result.url, title=top.result.title, reason="ranked_top")

    if input.mode == "validated":
        top = ranked[0]
        page = fetch_page(FetchPageInput(url=top.result.url))
        v = validate_docs_llm(ValidateDocsLLMInput(url=page.url, content=page.content, model=input.llm_model)) if page else None
        if v and v.is_docs:
            return FindDocsOutput(url=page.url, title=top.result.title, reason="validated_llm")
        return FindDocsOutput(url=top.result.url, title=top.result.title, reason="fallback_ranked")

    if input.mode == "cracked":
        # Use LLM re-ranking on top K, then validate LLM
        top_candidates = [r.result for r in ranked[: input.top_k]]
        picked = rank_docs_llm(RankDocsLLMInput(technology=input.technology, candidates=top_candidates, model=input.llm_model))
        if picked.url:
            page = fetch_page(FetchPageInput(url=picked.url))
            v = validate_docs_llm(ValidateDocsLLMInput(url=page.url, content=page.content, model=input.llm_model)) if page else None
            if v and v.is_docs:
                return FindDocsOutput(url=page.url, title=None, reason="llm_ranked_validated")
            return FindDocsOutput(url=picked.url, title=None, reason="llm_ranked")
        # If LLM fails, fallback to fast
        top = ranked[0]
        return FindDocsOutput(url=top.result.url, title=top.result.title, reason="fallback_ranked")

    # Default fallback
    top = ranked[0]
    return FindDocsOutput(url=top.result.url, title=top.result.title, reason="ranked_top")
