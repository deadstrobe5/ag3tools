from typing import Optional

from pydantic import BaseModel, Field
from ag3tools.core.registry import register_tool
from ag3tools.core.types import ToolResult


class ValidateDocsLLMInput(BaseModel):
    url: str = Field(..., description="Page URL")
    content: Optional[str] = Field(None, description="Fetched page text content")
    model: str = Field(default="gpt-4o-mini", description="LLM model to use")


class ValidateDocsLLMOutput(ToolResult):
    url: str = ""
    is_docs: bool = False
    reason: Optional[str] = None


def _import_openai():
    try:
        from openai import OpenAI  # type: ignore
        return OpenAI
    except Exception:  # pragma: no cover
        return None


@register_tool(
    description="Use an LLM to validate whether a page is the official docs (heuristic check).",
    input_model=ValidateDocsLLMInput,
    output_model=ValidateDocsLLMOutput,
    tags=["docs", "llm", "validation"],
    llm_expected_tokens=500,
)
def validate_docs_llm(input: ValidateDocsLLMInput) -> ValidateDocsLLMOutput:
    OpenAI = _import_openai()
    if OpenAI is None:
        return ValidateDocsLLMOutput(url=input.url, is_docs=False, reason="no_openai")

    client = OpenAI()
    text = (input.content or "")[:8000]
    prompt = (
        "You are verifying if a web page is the official documentation for a technology.\n"
        "Return strictly one of: YES or NO, then a short reason on the next line.\n"
        "Signals: docs engines (Docusaurus/MkDocs/Sphinx), sidebar, search docs input, API reference, version selector, canonical link.\n"
        f"URL: {input.url}\n\n"
        f"CONTENT:\n{text}"
    )
    resp = client.chat.completions.create(
        model=input.model,
        messages=[
            {"role": "system", "content": "Answer with 'YES' or 'NO' only on first line."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    content = (resp.choices[0].message.content or "").strip().splitlines()
    verdict = content[0].strip().upper() if content else "NO"
    reason = content[1].strip() if len(content) > 1 else None
    return ValidateDocsLLMOutput(url=input.url, is_docs=(verdict == "YES"), reason=reason)
