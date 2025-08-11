from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    title: str = Field(default="")
    url: str = Field(default="")
    snippet: str = Field(default="")


class RankedResult(BaseModel):
    result: SearchResult
    score: float


class WebSearchInput(BaseModel):
    query: str
    max_results: int = 12


class RankDocsInput(BaseModel):
    technology: str
    candidates: List[SearchResult]


class FindDocsInput(BaseModel):
    technology: str
    mode: Literal["fast", "validated", "cracked"] = "fast"
    top_k: int = 6
    llm_model: str = "gpt-4o-mini"


class FindDocsOutput(BaseModel):
    url: Optional[str]
    title: Optional[str] = None
    reason: Optional[str] = None


