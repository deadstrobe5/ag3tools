"""Tests for the tool execution engine."""

import pytest
import asyncio
from unittest.mock import patch

from ag3tools.core.execution import ToolExecutionEngine, get_execution_engine
from ag3tools.core.registry import register_tool
from pydantic import BaseModel, Field


class TestInput(BaseModel):
    message: str = Field(..., description="Test message")


class TestLLMInput(BaseModel):
    query: str = Field(..., description="Test query for LLM tool")


def test_get_execution_engine():
    """Test that we can get the global execution engine."""
    engine = get_execution_engine()
    assert isinstance(engine, ToolExecutionEngine)


def test_execution_engine_sync_tool():
    """Test executing a simple sync tool through the engine."""

    @register_tool(
        name="test_sync_tool",
        description="Test sync tool",
        input_model=TestInput,
        tags=[]
    )
    def test_sync_tool(input: TestInput):
        return {"message": f"Hello {input.message}"}

    from ag3tools.core.registry import get_tool_spec

    engine = ToolExecutionEngine()
    spec = get_tool_spec("test_sync_tool")

    result = engine.execute(spec, message="World")
    assert result["message"] == "Hello World"


def test_execution_engine_async_tool():
    """Test executing an async tool through the engine."""

    @register_tool(
        name="test_async_tool",
        description="Test async tool",
        input_model=TestInput,
        tags=[]
    )
    async def test_async_tool(input: TestInput):
        return {"message": f"Async hello {input.message}"}

    from ag3tools.core.registry import get_tool_spec

    async def run_test():
        engine = ToolExecutionEngine()
        spec = get_tool_spec("test_async_tool")

        result = await engine.execute_async(spec, message="World")
        assert result["message"] == "Async hello World"

    asyncio.run(run_test())


def test_execution_engine_sync_in_async_context():
    """Test executing a sync tool in async context (should use thread pool)."""

    @register_tool(
        name="test_sync_in_async",
        description="Test sync tool in async context",
        input_model=TestInput,
        tags=[]
    )
    def test_sync_in_async(input: TestInput):
        return {"message": f"Sync in async {input.message}"}

    from ag3tools.core.registry import get_tool_spec

    async def run_test():
        engine = ToolExecutionEngine()
        spec = get_tool_spec("test_sync_in_async")

        result = await engine.execute_async(spec, message="World")
        assert result["message"] == "Sync in async World"

    asyncio.run(run_test())


@patch('ag3tools.core.execution.settings.COST_LOG_ENABLED', True)
@patch('ag3tools.core.execution.ensure_openai_patched')
@patch('ag3tools.core.execution.start_capture')
@patch('ag3tools.core.execution.stop_capture')
@patch('ag3tools.core.execution.log_cost')
def test_execution_engine_llm_tracking(mock_log_cost, mock_stop_capture, mock_start_capture, mock_ensure_patched):
    """Test that LLM tracking works correctly."""

    # Mock the token tracking
    mock_stop_capture.return_value = {
        "gpt-4": (100, 50)  # input_tokens, output_tokens
    }

    @register_tool(
        name="test_llm_tool",
        description="Test LLM tool",
        input_model=TestLLMInput,
        tags=["llm"]
    )
    def test_llm_tool(input: TestLLMInput):
        return {"response": f"LLM response to {input.query}"}

    from ag3tools.core.registry import get_tool_spec

    engine = ToolExecutionEngine()
    spec = get_tool_spec("test_llm_tool")

    result = engine.execute(spec, query="test query")

    # Verify LLM tracking was set up
    mock_ensure_patched.assert_called_once()
    mock_start_capture.assert_called_once()
    mock_stop_capture.assert_called_once()
    mock_log_cost.assert_called_once()

    # Verify result
    assert result["response"] == "LLM response to test query"


@patch('ag3tools.core.execution.settings.COST_LOG_ENABLED', True)
@patch('ag3tools.core.execution.ensure_openai_patched')
@patch('ag3tools.core.execution.start_capture')
@patch('ag3tools.core.execution.stop_capture')
@patch('ag3tools.core.execution.log_cost')
def test_execution_engine_async_llm_tracking(mock_log_cost, mock_stop_capture, mock_start_capture, mock_ensure_patched):
    """Test that async LLM tracking works correctly."""

    # Mock the token tracking
    mock_stop_capture.return_value = {
        "gpt-4": (150, 75)  # input_tokens, output_tokens
    }

    @register_tool(
        name="test_async_llm_tool",
        description="Test async LLM tool",
        input_model=TestLLMInput,
        tags=["llm"]
    )
    async def test_async_llm_tool(input: TestLLMInput):
        return {"response": f"Async LLM response to {input.query}"}

    from ag3tools.core.registry import get_tool_spec

    async def run_test():
        engine = ToolExecutionEngine()
        spec = get_tool_spec("test_async_llm_tool")

        result = await engine.execute_async(spec, query="async test query")

        # Verify LLM tracking was set up
        mock_ensure_patched.assert_called_once()
        mock_start_capture.assert_called_once()
        mock_stop_capture.assert_called_once()
        mock_log_cost.assert_called_once()

        # Verify result
        assert result["response"] == "Async LLM response to async test query"

    asyncio.run(run_test())


def test_execution_engine_non_llm_tool_no_tracking():
    """Test that non-LLM tools don't trigger tracking."""

    @register_tool(
        name="test_non_llm_tool",
        description="Test non-LLM tool",
        input_model=TestInput,
        tags=[]  # No "llm" tag
    )
    def test_non_llm_tool(input: TestInput):
        return {"message": f"Non-LLM {input.message}"}

    from ag3tools.core.registry import get_tool_spec

    with patch('ag3tools.core.execution.ensure_openai_patched') as mock_ensure_patched:
        engine = ToolExecutionEngine()
        spec = get_tool_spec("test_non_llm_tool")

        result = engine.execute(spec, message="test")

        # Verify no LLM tracking was set up
        mock_ensure_patched.assert_not_called()

        # Verify result
        assert result["message"] == "Non-LLM test"


def test_execution_engine_error_handling():
    """Test that execution engine properly handles and propagates errors."""

    @register_tool(
        name="test_error_tool",
        description="Test tool that raises an error",
        input_model=TestInput,
        tags=[]
    )
    def test_error_tool(input: TestInput):
        raise ValueError("Test error")

    from ag3tools.core.registry import get_tool_spec

    engine = ToolExecutionEngine()
    spec = get_tool_spec("test_error_tool")

    with pytest.raises(ValueError, match="Test error"):
        engine.execute(spec, message="test")


def test_execution_engine_async_error_handling():
    """Test that async execution engine properly handles and propagates errors."""

    @register_tool(
        name="test_async_error_tool",
        description="Test async tool that raises an error",
        input_model=TestInput,
        tags=[]
    )
    async def test_async_error_tool(input: TestInput):
        raise RuntimeError("Async test error")

    from ag3tools.core.registry import get_tool_spec

    async def run_test():
        engine = ToolExecutionEngine()
        spec = get_tool_spec("test_async_error_tool")

        with pytest.raises(RuntimeError, match="Async test error"):
            await engine.execute_async(spec, message="test")

    asyncio.run(run_test())
