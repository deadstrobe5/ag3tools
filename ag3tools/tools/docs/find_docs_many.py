from typing import List

from ag3tools.core.types import BaseModel, Field, FindDocsOutput
from ag3tools.core.registry import register_tool
from ag3tools.tools.docs.find_docs import find_docs


class FindDocsManyInput(BaseModel):
    technologies: List[str] = Field(..., description="List of technology names")


@register_tool(
    description="Find documentation URLs for many technologies (batched).",
    input_model=FindDocsManyInput,
    tags=["docs", "batch"],
)
def find_docs_many(input: FindDocsManyInput) -> List[FindDocsOutput]:
    outs: List[FindDocsOutput] = []
    for tech in input.technologies:
        out = find_docs(type("_", (), {"technology": tech})())
        outs.append(out)
    return outs


