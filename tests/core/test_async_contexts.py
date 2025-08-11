import asyncio
import pytest
from ag3tools.core.llm_instrumentation import start_capture, stop_capture, _get_agg, _token_context, _prev_context


def test_sync_context_isolation():
    """Test that sync contexts don't interfere with each other."""
    # Clean slate
    _token_context.set({})
    _prev_context.set(None)

    # First context
    start_capture()
    agg1 = _get_agg()
    agg1['model-1'] = (100, 50)
    result1 = stop_capture()

    # Second context
    start_capture()
    agg2 = _get_agg()
    agg2['model-2'] = (200, 75)
    result2 = stop_capture()

    # Verify isolation
    assert result1 == {'model-1': (100, 50)}
    assert result2 == {'model-2': (200, 75)}

    # Verify contexts are clean after stop
    assert _get_agg() == {}


@pytest.mark.asyncio
async def test_async_context_isolation():
    """Test that async contexts are properly isolated."""

    async def worker(worker_id: int, input_tokens: int, output_tokens: int):
        start_capture()
        agg = _get_agg()
        agg[f'model-{worker_id}'] = (input_tokens, output_tokens)

        # Simulate async work
        await asyncio.sleep(0.01)

        # Verify our data is still there
        assert _get_agg()[f'model-{worker_id}'] == (input_tokens, output_tokens)

        result = stop_capture()
        return result

    # Run multiple workers concurrently
    tasks = [
        worker(1, 100, 50),
        worker(2, 200, 75),
        worker(3, 300, 100)
    ]

    results = await asyncio.gather(*tasks)

    # Verify each worker got its own isolated data
    expected_results = [
        {'model-1': (100, 50)},
        {'model-2': (200, 75)},
        {'model-3': (300, 100)}
    ]

    assert results == expected_results


@pytest.mark.asyncio
async def test_nested_async_contexts():
    """Test that nested async capture/stop calls work correctly."""

    async def outer_context():
        start_capture()
        agg = _get_agg()
        agg['outer'] = (100, 50)

        # Inner context
        inner_result = await inner_context()

        # Verify outer context is restored
        assert _get_agg()['outer'] == (100, 50)
        return stop_capture(), inner_result

    async def inner_context():
        start_capture()
        agg = _get_agg()
        agg['inner'] = (200, 75)

        await asyncio.sleep(0.01)
        return stop_capture()

    outer_result, inner_result = await outer_context()

    assert outer_result == {'outer': (100, 50)}
    assert inner_result == {'inner': (200, 75)}


def test_context_restoration():
    """Test that previous context is properly restored after stop_capture."""
    # Clean slate
    _token_context.set({})
    _prev_context.set(None)

    # Set up initial context
    start_capture()
    agg = _get_agg()
    agg['initial'] = (50, 25)

    # Nested context
    start_capture()
    nested_agg = _get_agg()
    nested_agg['nested'] = (100, 50)
    nested_result = stop_capture()

    # Verify nested result and context restoration
    assert nested_result == {'nested': (100, 50)}
    assert _get_agg() == {'initial': (50, 25)}

    # Clean up
    final_result = stop_capture()
    assert final_result == {'initial': (50, 25)}
    assert _get_agg() == {}


@pytest.mark.asyncio
async def test_concurrent_mixed_sync_async():
    """Test that sync and async contexts don't interfere."""

    def sync_worker():
        start_capture()
        agg = _get_agg()
        agg['sync'] = (150, 60)
        return stop_capture()

    async def async_worker():
        start_capture()
        agg = _get_agg()
        agg['async'] = (250, 80)
        await asyncio.sleep(0.01)
        return stop_capture()

    # Run sync work in thread and async work concurrently
    async_task = asyncio.create_task(async_worker())
    sync_result = await asyncio.to_thread(sync_worker)
    async_result = await async_task

    assert sync_result == {'sync': (150, 60)}
    assert async_result == {'async': (250, 80)}


def test_empty_context_behavior():
    """Test behavior with empty contexts."""
    # Clean slate
    _token_context.set({})
    _prev_context.set(None)

    # Test stop without start
    result = stop_capture()
    assert result == {}

    # Test start/stop with no data
    start_capture()
    result = stop_capture()
    assert result == {}

    # Test get_agg with no context
    assert _get_agg() == {}


@pytest.mark.asyncio
async def test_exception_handling_in_contexts():
    """Test that contexts remain if stop_capture isn't called due to exceptions."""
    # Clean slate
    _token_context.set({})
    _prev_context.set(None)

    async def failing_worker():
        start_capture()
        agg = _get_agg()
        agg['failing'] = (100, 50)

        # This should still capture the tokens before the exception
        await asyncio.sleep(0.01)
        raise ValueError("Test exception")

    # Even though this fails, the context should be isolated
    with pytest.raises(ValueError):
        await failing_worker()

    # Context remains dirty because stop_capture() was never called
    assert _get_agg() == {'failing': (100, 50)}

    # But we can clean up and continue with new operations
    _token_context.set({})
    _prev_context.set(None)

    start_capture()
    agg = _get_agg()
    agg['after_exception'] = (200, 75)
    result = stop_capture()
    assert result == {'after_exception': (200, 75)}
    assert _get_agg() == {}
