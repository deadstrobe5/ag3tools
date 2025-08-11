from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type

from pydantic import BaseModel
from ag3tools.core.execution import get_execution_engine



@dataclass
class ToolSpec:
    name: str
    description: str
    input_model: Type[BaseModel]
    output_model: Optional[Type[BaseModel]]
    fn: Callable[[Any], Any]
    tags: List[str]
    llm_expected_tokens: Optional[int]


_REGISTRY: Dict[str, ToolSpec] = {}


def register_tool(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    input_model: Type[BaseModel],
    output_model: Optional[Type[BaseModel]] = None,
    tags: Optional[List[str]] = None,
    llm_expected_tokens: Optional[int] = None,
):
    def _decorator(fn: Callable[[Any], Any]):
        tool_name = name or fn.__name__
        desc = (description or fn.__doc__ or "").strip()
        _REGISTRY[tool_name] = ToolSpec(
            name=tool_name,
            description=desc,
            input_model=input_model,
            output_model=output_model,
            fn=fn,
            tags=list(tags or []),
            llm_expected_tokens=llm_expected_tokens,
        )
        return fn
    return _decorator


def list_tools() -> List[ToolSpec]:
    return list(_REGISTRY.values())


def get_tool_spec(name: str) -> ToolSpec:
    return _REGISTRY[name]


def invoke_tool(name: str, **kwargs):
    """Execute a tool synchronously."""
    spec = get_tool_spec(name)
    execution_engine = get_execution_engine()
    return execution_engine.execute(spec, **kwargs)


def tool_summaries() -> List[dict]:
    return [
        {
            "name": spec.name,
            "description": spec.description,
            "parameters": spec.input_model.schema(),
            "tags": list(spec.tags),
            "llm_expected_tokens": spec.llm_expected_tokens,
        }
        for spec in list_tools()
    ]


async def invoke_tool_async(name: str, **kwargs):
    """Execute a tool asynchronously."""
    spec = get_tool_spec(name)
    execution_engine = get_execution_engine()
    return await execution_engine.execute_async(spec, **kwargs)
