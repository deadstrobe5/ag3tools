from pydantic import BaseModel, Field
from ag3tools.tools.docs.find_docs import FindDocsOutput, FindDocsInput
from ag3tools.core.registry import register_tool
from ag3tools.tools.docs.find_docs import find_docs
from ag3tools.tools.net.fetch_page import fetch_page, FetchPageInput
from ag3tools.tools.docs.validate_docs import validate_docs_page, ValidateDocsInput


class FindDocsValidatedInput(BaseModel):
    technology: str = Field(..., description="Technology name")


@register_tool(
    description="Find docs and validate the top candidate by fetching content and checking docs signals.",
    input_model=FindDocsValidatedInput,
    tags=["docs", "validation"],
)
def find_docs_validated(input: FindDocsValidatedInput) -> FindDocsOutput:
    base = find_docs(FindDocsInput(technology=input.technology))
    page = fetch_page(FetchPageInput(url=base.url)) if base.url else None
    if page and page.content:
        v = validate_docs_page(ValidateDocsInput(url=page.url, content=page.content))
        if v.is_docs:
            return FindDocsOutput(url=page.url, title=base.title, reason="validated")
    return base
