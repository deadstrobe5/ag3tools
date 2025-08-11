from typing import Optional
import httpx

from pydantic import BaseModel, Field
from ag3tools.core.registry import register_tool
from ag3tools.core.settings import HTTP_TIMEOUT_SECONDS
from ag3tools.core.types import ToolResult


class FetchPageInput(BaseModel):
    url: str = Field(..., description="URL to fetch")


class FetchPageOutput(ToolResult):
    url: str
    status: int = 0
    content: Optional[str] = None
    content_type: Optional[str] = None


@register_tool(
    description="Fetch a web page with a short timeout; returns status, content, and content-type.",
    input_model=FetchPageInput,
    output_model=FetchPageOutput,
    tags=["net"],
)
def fetch_page(input: FetchPageInput) -> FetchPageOutput:
    try:
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = client.get(input.url, headers={"User-Agent": "ag3tools/0.1"})
            content_type = resp.headers.get("content-type")
            text = None
            if content_type and "text" in content_type:
                text = resp.text
            return FetchPageOutput(url=str(resp.url), status=resp.status_code, content=text, content_type=content_type)
    except Exception as e:
        return FetchPageOutput(
            success=False,
            error_message=f"Failed to fetch {input.url}: {str(e)}",
            error_code="FETCH_ERROR",
            url=input.url
        )


@register_tool(
    description="Async variant of fetch_page.",
    input_model=FetchPageInput,
    output_model=FetchPageOutput,
    tags=["net", "async"],
)
async def fetch_page_async(input: FetchPageInput) -> FetchPageOutput:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = await client.get(input.url, headers={"User-Agent": "ag3tools/0.1"})
            content_type = resp.headers.get("content-type")
            text = None
            if content_type and "text" in content_type:
                text = resp.text
            return FetchPageOutput(url=str(resp.url), status=resp.status_code, content=text, content_type=content_type)
    except Exception as e:
        return FetchPageOutput(
            success=False,
            error_message=f"Failed to fetch {input.url}: {str(e)}",
            error_code="FETCH_ERROR",
            url=input.url
        )
