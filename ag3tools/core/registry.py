from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Type
import asyncio
import inspect
import time

from pydantic import BaseModel
from ag3tools.core.llm_instrumentation import ensure_openai_patched, start_capture, stop_capture
from ag3tools.core.cost import log_cost, CostEvent, estimate_openai_cost
from ag3tools.core import settings



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


def _log_llm_costs(start_time: float, tool_name: str) -> None:
    """Helper to log LLM costs from captured token usage."""
    if not settings.COST_LOG_ENABLED:
        return

    agg = stop_capture()
    for model, (in_t, out_t) in agg.items():
        ic, oc, total, cur = estimate_openai_cost(model, in_t, out_t)
        log_cost(CostEvent(
            ts=start_time,
            tool=tool_name,
            model=model,
            input_tokens=in_t,
            output_tokens=out_t,
            currency=cur,
            input_cost=ic,
            output_cost=oc,
            total_cost=total,
            meta={}
        ))


def _execute_with_llm_tracking(fn, model_instance, spec):
    """Execute function with LLM cost tracking if needed."""
    if "llm" not in spec.tags:
        return fn(model_instance)

    ensure_openai_patched()
    start_capture()
    t0 = time.time()

    try:
        result = fn(model_instance)
        _log_llm_costs(t0, spec.name)
        return result
    except Exception:
        _log_llm_costs(t0, spec.name)
        raise


async def _execute_async_with_llm_tracking(fn, model_instance, spec):
    """Execute async function with LLM cost tracking if needed."""
    if "llm" not in spec.tags:
        return await fn(model_instance)

    ensure_openai_patched()
    start_capture()
    t0 = time.time()

    try:
        result = await fn(model_instance)
        _log_llm_costs(t0, spec.name)
        return result
    except Exception:
        _log_llm_costs(t0, spec.name)
        raise


def invoke_tool(name: str, **kwargs):
    spec = get_tool_spec(name)
    model_instance = spec.input_model(**kwargs)
    return _execute_with_llm_tracking(spec.fn, model_instance, spec)


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
    spec = get_tool_spec(name)
    model_instance = spec.input_model(**kwargs)

    if inspect.iscoroutinefunction(spec.fn):
        return await _execute_async_with_llm_tracking(spec.fn, model_instance, spec)
    else:
        # run sync function in thread to avoid blocking
        if "llm" in spec.tags:
            ensure_openai_patched()
            start_capture()
            t0 = time.time()

            try:
                result = await asyncio.to_thread(spec.fn, model_instance)
                _log_llm_costs(t0, spec.name)
                return result
            except Exception:
                _log_llm_costs(t0, spec.name)
                raise
        else:
            return await asyncio.to_thread(spec.fn, model_instance)
