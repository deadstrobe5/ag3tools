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


def invoke_tool(name: str, **kwargs):
    spec = get_tool_spec(name)
    model_instance = spec.input_model(**kwargs)
    if "llm" in spec.tags:
        ensure_openai_patched()
        start_capture()
        t0 = time.time()
        result = spec.fn(model_instance)
        agg = stop_capture()
        if settings.COST_LOG_ENABLED:
            for model, (in_t, out_t) in agg.items():
                ic, oc, total, cur = estimate_openai_cost(model, in_t, out_t)
                log_cost(CostEvent(ts=t0, tool=spec.name, model=model, input_tokens=in_t, output_tokens=out_t, currency=cur, input_cost=ic, output_cost=oc, total_cost=total, meta={}))
        return result
    return spec.fn(model_instance)


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
        if "llm" in spec.tags:
            ensure_openai_patched()
            start_capture()
            t0 = time.time()
            result = await spec.fn(model_instance)
            agg = stop_capture()
            if settings.COST_LOG_ENABLED:
                for model, (in_t, out_t) in agg.items():
                    ic, oc, total, cur = estimate_openai_cost(model, in_t, out_t)
                    log_cost(CostEvent(ts=t0, tool=spec.name, model=model, input_tokens=in_t, output_tokens=out_t, currency=cur, input_cost=ic, output_cost=oc, total_cost=total, meta={}))
            return result
        return await spec.fn(model_instance)
    # run sync function in thread to avoid blocking
    if "llm" in spec.tags:
        ensure_openai_patched()
        start_capture()
        t0 = time.time()
        result = await asyncio.to_thread(spec.fn, model_instance)
        agg = stop_capture()
        if settings.COST_LOG_ENABLED:
            for model, (in_t, out_t) in agg.items():
                ic, oc, total, cur = estimate_openai_cost(model, in_t, out_t)
                log_cost(CostEvent(ts=t0, tool=spec.name, model=model, input_tokens=in_t, output_tokens=out_t, currency=cur, input_cost=ic, output_cost=oc, total_cost=total, meta={}))
        return result
    return await asyncio.to_thread(spec.fn, model_instance)
