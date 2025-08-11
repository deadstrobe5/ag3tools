from typing import List, Optional

from pydantic import BaseModel, Field
from ag3tools.tools.search.web_search import SearchResult
from ag3tools.core.registry import register_tool


class RankDocsLLMInput(BaseModel):
    technology: str = Field(..., description="Technology name")
    candidates: List[SearchResult] = Field(..., description="Candidate results to re-rank")
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")


class RankDocsLLMOutput(BaseModel):
    url: Optional[str]
    reason: Optional[str] = None


@register_tool(
    description="Use an LLM to pick the best official docs URL from candidates.",
    input_model=RankDocsLLMInput,
    output_model=RankDocsLLMOutput,
    tags=["docs", "llm", "ranking"],
    llm_expected_tokens=350,
)
def rank_docs_llm(input: RankDocsLLMInput) -> RankDocsLLMOutput:
    try:
        from openai import Client  # type: ignore
    except ImportError:
        return RankDocsLLMOutput(url=None, reason="no_openai")

    client = Client()
    lines = []
    for i, c in enumerate(input.candidates, 1):
        lines.append(f"{i}. title={c.title}\n   url={c.url}\n   snippet={c.snippet}")
    prompt = (
        "You are ranking web results to find the OFFICIAL documentation homepage for a technology.\n"
        f"Technology: {input.technology}\n"
        "Choose ONE URL from the list that is most likely the official docs landing page.\n"
        "Prefer domains like docs.*, readthedocs, github.io, official site /docs, Docusaurus/MkDocs/Sphinx pages.\n"
        "Return ONLY the URL.\n\n"
        + "\n".join(lines)
    )

    resp = client.chat.completions.create(
        model=input.model,
        messages=[
            {"role": "system", "content": "You return only the winning URL"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    content = (resp.choices[0].message.content or "").strip()
    # Extract first URL-like token
    url = None
    for token in content.split():
        if token.startswith("http://") or token.startswith("https://"):
            url = token.strip().rstrip(".,)")
            break
    return RankDocsLLMOutput(url=url, reason="llm_ranked")
