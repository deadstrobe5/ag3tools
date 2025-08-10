from typing import List, Optional
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


class FindDocsOutput(BaseModel):
    url: Optional[str]
    title: Optional[str] = None
    reason: Optional[str] = None


