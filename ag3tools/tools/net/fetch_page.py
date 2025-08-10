from typing import Optional
import httpx

from ag3tools.core.types import BaseModel, Field
from ag3tools.core.registry import register_tool
from ag3tools.core.settings import HTTP_TIMEOUT_SECONDS


class FetchPageInput(BaseModel):
    url: str = Field(..., description="URL to fetch")


class FetchPageOutput(BaseModel):
    url: str
    status: int
    content: Optional[str]
    content_type: Optional[str]


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
    except Exception:
        return FetchPageOutput(url=input.url, status=0, content=None, content_type=None)


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
    except Exception:
        return FetchPageOutput(url=input.url, status=0, content=None, content_type=None)
