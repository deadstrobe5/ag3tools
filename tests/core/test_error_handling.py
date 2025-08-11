from ag3tools.core.registry import invoke_tool
from ag3tools.core.types import ToolResult


def test_successful_tool_returns_success_true():
    """Test that successful tools return success=True."""
    result = invoke_tool('web_search', query='python', max_results=1)
    assert result.success is True
    assert result.error_message is None
    assert result.error_code is None


def test_fetch_page_error_handling():
    """Test that fetch_page returns proper error format."""
    result = invoke_tool('fetch_page', url='invalid-url')

    assert result.success is False
    assert result.error_code == 'FETCH_ERROR'
    assert 'Failed to fetch invalid-url' in result.error_message
    assert result.url == 'invalid-url'  # Should still have the input URL


def test_fetch_page_invalid_protocol():
    """Test fetch_page with invalid protocol."""
    result = invoke_tool('fetch_page', url='ftp://example.com')

    assert result.success is False
    assert result.error_code == 'FETCH_ERROR'
    assert 'unsupported protocol' in result.error_message.lower()


def test_web_search_success_format():
    """Test that web_search returns proper success format."""
    result = invoke_tool('web_search', query='test', max_results=2)

    assert result.success is True
    assert hasattr(result, 'results')
    assert isinstance(result.results, list)
    assert result.error_message is None
    assert result.error_code is None


def test_find_docs_no_results():
    """Test find_docs when no results are found."""
    # Use a very unlikely search term
    result = invoke_tool('find_docs', technology='zzzznonexistenttech999')

    # This might succeed with some random result or fail - either is valid
    if not result.success:
        assert result.error_code == 'NO_RESULTS'
        assert 'No documentation found' in result.error_message
        assert result.reason == 'no_results'


def test_all_tools_have_success_field():
    """Test that all tools return objects with success field."""
    tools_to_test = [
        ('web_search', {'query': 'test', 'max_results': 1}),
        ('fetch_page', {'url': 'https://httpbin.org/get'}),
        ('find_docs', {'technology': 'python'}),
    ]

    for tool_name, params in tools_to_test:
        result = invoke_tool(tool_name, **params)
        assert hasattr(result, 'success'), f'{tool_name} result missing success field'
        assert isinstance(result.success, bool), f'{tool_name} success field is not boolean'


def test_error_fields_are_optional():
    """Test that error fields are None when success=True."""
    result = invoke_tool('web_search', query='python', max_results=1)

    assert result.success is True
    assert result.error_message is None
    assert result.error_code is None


def test_error_fields_populated_on_failure():
    """Test that error fields are populated when success=False."""
    result = invoke_tool('fetch_page', url='invalid://url')

    assert result.success is False
    assert result.error_message is not None
    assert result.error_code is not None
    assert isinstance(result.error_message, str)
    assert isinstance(result.error_code, str)


def test_tool_result_base_class_error_method():
    """Test the ToolResult.error() class method."""
    error_result = ToolResult.error("Test error message", "TEST_CODE")

    assert error_result.success is False
    assert error_result.error_message == "Test error message"
    assert error_result.error_code == "TEST_CODE"


def test_tool_result_base_class_defaults():
    """Test ToolResult default values."""
    result = ToolResult()

    assert result.success is True
    assert result.error_message is None
    assert result.error_code is None
    assert result.metadata == {}


def test_consistent_error_checking_pattern():
    """Test that the consistent error checking pattern works."""

    def check_result(result):
        """Helper function that uses the standard error checking pattern."""
        if not result.success:
            return f"Error [{result.error_code}]: {result.error_message}"
        return "Success"

    # Test successful case
    success_result = invoke_tool('web_search', query='test', max_results=1)
    assert check_result(success_result) == "Success"

    # Test error case
    error_result = invoke_tool('fetch_page', url='invalid-url')
    error_msg = check_result(error_result)
    assert error_msg.startswith("Error [FETCH_ERROR]:")
    assert "Failed to fetch invalid-url" in error_msg


def test_async_tools_have_same_error_handling():
    """Test that async tools follow the same error handling pattern."""
    import asyncio
    from ag3tools.core.registry import invoke_tool_async

    async def test_async_error():
        result = await invoke_tool_async('fetch_page_async', url='invalid-url')
        assert result.success is False
        assert result.error_code == 'FETCH_ERROR'
        assert 'Failed to fetch invalid-url' in result.error_message

    async def test_async_success():
        result = await invoke_tool_async('web_search_async', query='test', max_results=1)
        assert result.success is True
        assert result.error_message is None

    # Run async tests
    asyncio.run(test_async_error())
    asyncio.run(test_async_success())


def test_tool_specific_fields_preserved():
    """Test that tool-specific fields are preserved alongside error handling."""

    # Successful fetch should have all fields
    success_result = invoke_tool('fetch_page', url='https://httpbin.org/get')
    assert success_result.success is True
    assert hasattr(success_result, 'url')
    assert hasattr(success_result, 'status')
    assert hasattr(success_result, 'content_type')

    # Failed fetch should still have URL field
    error_result = invoke_tool('fetch_page', url='invalid-url')
    assert error_result.success is False
    assert hasattr(error_result, 'url')
    assert error_result.url == 'invalid-url'


def test_metadata_field_available():
    """Test that metadata field is available on all results."""
    result = invoke_tool('web_search', query='test', max_results=1)
    assert hasattr(result, 'metadata')
    assert isinstance(result.metadata, dict)
