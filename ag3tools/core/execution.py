"""Tool execution engine for ag3tools.

Handles the execution of tools with middleware support for LLM tracking,
cost logging, error handling, and future extensibility.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, Optional



from ag3tools.core.llm_instrumentation import ensure_openai_patched, start_capture, stop_capture
from ag3tools.core.cost import log_cost, CostEvent, estimate_openai_cost
from ag3tools.core import settings


class ToolExecutionEngine:
    """Engine responsible for executing tools with middleware support."""

    def __init__(self):
        pass

    def execute(self, spec, **kwargs) -> Any:
        """Execute a tool synchronously with all middleware."""
        model_instance = spec.input_model(**kwargs)
        return self._execute_with_llm_tracking(spec.fn, model_instance, spec)

    async def execute_async(self, spec, **kwargs) -> Any:
        """Execute a tool asynchronously with all middleware."""
        model_instance = spec.input_model(**kwargs)

        if inspect.iscoroutinefunction(spec.fn):
            return await self._execute_async_with_llm_tracking(spec.fn, model_instance, spec)
        else:
            # run sync function in thread to avoid blocking
            if "llm" in spec.tags:
                ensure_openai_patched()
                start_capture()
                t0 = time.time()

                # Capture tool parameters for logging
                tool_params = model_instance.model_dump() if hasattr(model_instance, 'model_dump') else {}

                try:
                    result = await asyncio.to_thread(spec.fn, model_instance)
                    execution_time_ms = (time.time() - t0) * 1000
                    self._log_llm_costs(t0, spec.name, tool_params, execution_time_ms)
                    return result
                except Exception:
                    execution_time_ms = (time.time() - t0) * 1000
                    self._log_llm_costs(t0, spec.name, tool_params, execution_time_ms)
                    raise
            else:
                return await asyncio.to_thread(spec.fn, model_instance)

    def _execute_with_llm_tracking(self, fn, model_instance, spec):
        """Execute function with LLM cost tracking if needed."""
        if "llm" not in spec.tags:
            return fn(model_instance)

        ensure_openai_patched()
        start_capture()
        t0 = time.time()

        # Capture tool parameters for logging
        tool_params = model_instance.model_dump() if hasattr(model_instance, 'model_dump') else {}

        try:
            result = fn(model_instance)
            execution_time_ms = (time.time() - t0) * 1000
            self._log_llm_costs(t0, spec.name, tool_params, execution_time_ms)
            return result
        except Exception:
            execution_time_ms = (time.time() - t0) * 1000
            self._log_llm_costs(t0, spec.name, tool_params, execution_time_ms)
            raise

    async def _execute_async_with_llm_tracking(self, fn, model_instance, spec):
        """Execute async function with LLM cost tracking if needed."""
        if "llm" not in spec.tags:
            return await fn(model_instance)

        ensure_openai_patched()
        start_capture()
        t0 = time.time()

        # Capture tool parameters for logging
        tool_params = model_instance.model_dump() if hasattr(model_instance, 'model_dump') else {}

        try:
            result = await fn(model_instance)
            execution_time_ms = (time.time() - t0) * 1000
            self._log_llm_costs(t0, spec.name, tool_params, execution_time_ms)
            return result
        except Exception:
            execution_time_ms = (time.time() - t0) * 1000
            self._log_llm_costs(t0, spec.name, tool_params, execution_time_ms)
            raise

    def _log_llm_costs(self, start_time: float, tool_name: str, tool_params: Optional[dict] = None, execution_time_ms: Optional[float] = None) -> None:
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
                meta={},
                tool_params=tool_params,
                execution_time_ms=execution_time_ms
            ))


# Global execution engine instance
_execution_engine = ToolExecutionEngine()


def get_execution_engine() -> ToolExecutionEngine:
    """Get the global execution engine instance."""
    return _execution_engine
