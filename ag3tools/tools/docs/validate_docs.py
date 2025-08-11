import re
from typing import Optional

from pydantic import BaseModel, Field
from ag3tools.core.registry import register_tool


DOC_HINTS = [
    r"sidebar",
    r"search docs",
    r"api reference",
    r"table of contents",
    r"docsify|docusaurus|mkdocs|sphinx",
    r"class\s+\w+",
]


class ValidateDocsInput(BaseModel):
    url: str = Field(..., description="URL of the fetched page")
    content: Optional[str] = Field(None, description="Page text content")


class ValidateDocsOutput(BaseModel):
    url: str
    is_docs: bool
    reason: Optional[str] = None


@register_tool(
    description="Heuristically validate if a fetched page looks like documentation.",
    input_model=ValidateDocsInput,
    output_model=ValidateDocsOutput,
    tags=["docs", "validation"],
)
def validate_docs_page(input: ValidateDocsInput) -> ValidateDocsOutput:
    if not input.content:
        return ValidateDocsOutput(url=input.url, is_docs=False, reason="no_content")
    text = input.content.lower()
    for pattern in DOC_HINTS:
        if re.search(pattern, text):
            return ValidateDocsOutput(url=input.url, is_docs=True, reason=f"match:{pattern}")
    return ValidateDocsOutput(url=input.url, is_docs=False, reason="no_match")
