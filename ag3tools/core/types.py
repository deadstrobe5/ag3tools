from typing import Optional, List
from pydantic import BaseModel


class ToolMetadata(BaseModel):
    """Metadata for a tool."""
    name: str
    description: str
    tags: List[str] = []
    llm_expected_tokens: Optional[int] = None


class ToolResult(BaseModel):
    """Base result type with common fields."""
    success: bool = True
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    metadata: dict = {}

    @classmethod
    def error(cls, message: str, code: str = "ERROR", **kwargs) -> "ToolResult":
        """Create an error result."""
        return cls(success=False, error_message=message, error_code=code, **kwargs)
