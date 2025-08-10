from ag3tools.core.types import FindDocsInput, FindDocsOutput, RankDocsInput, WebSearchInput
from ag3tools.tools.search.web_search import web_search
from ag3tools.tools.docs.rank_docs import rank_docs
from ag3tools.core.registry import register_tool


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
        results.extend(web_search(WebSearchInput(query=q, max_results=10)))
    ranked = rank_docs(RankDocsInput(technology=input.technology, candidates=results))
    if not ranked:
        return FindDocsOutput(url=None, reason="no_results")
    top = ranked[0]
    return FindDocsOutput(url=top.result.url, title=top.result.title, reason="ranked_top")


