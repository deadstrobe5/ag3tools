import pytest
import io

from unittest.mock import patch
from ag3tools.core.cli import main, _print_tool_result, _print_json_result
from ag3tools.tools.search.web_search import WebSearchOutput, SearchResult
from ag3tools.tools.net.fetch_page import FetchPageOutput
from ag3tools.tools.docs.find_docs import FindDocsOutput


class TestCLIImprovements:
    """Test CLI output formatting improvements."""

    def test_web_search_output_formatting(self):
        """Test that web search results are formatted nicely."""
        results = [
            SearchResult(title="Python Tutorial", url="https://python.org", snippet="Learn Python"),
            SearchResult(title="Python Docs", url="https://docs.python.org", snippet="Official docs"),
            SearchResult(title="Python Guide", url="https://guide.python.org", snippet="Best practices")
        ]
        web_result = WebSearchOutput(success=True, results=results)

        # Capture stdout
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_tool_result(web_result)

        output = captured_output.getvalue()
        assert "Found 3 results:" in output
        assert "1. Python Tutorial" in output
        assert "https://python.org" in output
        assert "2. Python Docs" in output
        assert "3. Python Guide" in output

    def test_web_search_output_with_many_results(self):
        """Test that only first 3 results are shown with 'more' indicator."""
        results = [
            SearchResult(title=f"Result {i}", url=f"https://example{i}.com", snippet=f"Snippet {i}")
            for i in range(1, 6)  # 5 results
        ]
        web_result = WebSearchOutput(success=True, results=results)

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_tool_result(web_result)

        output = captured_output.getvalue()
        assert "Found 5 results:" in output
        assert "1. Result 1" in output
        assert "2. Result 2" in output
        assert "3. Result 3" in output
        assert "... and 2 more" in output
        assert "Result 4" not in output  # Should not show beyond first 3

    def test_web_search_empty_results(self):
        """Test formatting when no search results found."""
        web_result = WebSearchOutput(success=True, results=[])

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_tool_result(web_result)

        output = captured_output.getvalue()
        assert "No results found" in output

    def test_fetch_page_success_formatting(self):
        """Test that fetch page results are formatted nicely."""
        fetch_result = FetchPageOutput(
            success=True,
            url="https://example.com",
            status=200,
            content="<html>...</html>",
            content_type="text/html"
        )

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_tool_result(fetch_result)

        output = captured_output.getvalue()
        assert "Status: 200" in output
        assert "URL: https://example.com" in output
        assert "Content-Type: text/html" in output

    def test_fetch_page_without_content_type(self):
        """Test fetch page formatting without content type."""
        fetch_result = FetchPageOutput(
            success=True,
            url="https://example.com",
            status=200,
            content=None,
            content_type=None
        )

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_tool_result(fetch_result)

        output = captured_output.getvalue()
        assert "Status: 200" in output
        assert "URL: https://example.com" in output
        assert "Content-Type:" not in output

    def test_find_docs_success_formatting(self):
        """Test that find docs results show just the URL."""
        docs_result = FindDocsOutput(
            success=True,
            url="https://docs.example.com",
            title="Example Docs",
            reason="ranked_top"
        )

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_tool_result(docs_result)

        output = captured_output.getvalue().strip()
        assert output == "https://docs.example.com"

    def test_error_result_formatting(self):
        """Test that error results are formatted consistently."""
        error_result = FetchPageOutput(
            success=False,
            error_message="Connection timeout",
            error_code="TIMEOUT_ERROR",
            url="https://slow.example.com",
            status=0
        )

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_tool_result(error_result)

        output = captured_output.getvalue().strip()
        assert output == "Error [TIMEOUT_ERROR]: Connection timeout"

    def test_fallback_formatting(self):
        """Test fallback formatting for unknown result types."""
        class CustomResult:
            def __init__(self):
                self.success = True
                self.custom_field = "value"

            def __str__(self):
                return "CustomResult(custom_field='value')"

        custom_result = CustomResult()

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_tool_result(custom_result)

        output = captured_output.getvalue().strip()
        assert "CustomResult(custom_field='value')" in output

    def test_json_output_formatting(self):
        """Test that JSON output works correctly."""
        web_result = WebSearchOutput(
            success=True,
            results=[SearchResult(title="Test", url="https://test.com", snippet="Test snippet")]
        )

        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            _print_json_result(web_result)

        output = captured_output.getvalue()
        # Should be valid JSON
        import json
        parsed = json.loads(output)
        assert parsed['success'] is True
        assert len(parsed['results']) == 1
        assert parsed['results'][0]['title'] == "Test"


class TestCLICommands:
    """Test CLI command execution with improved output."""

    def test_run_command_with_success(self):
        """Test that run command shows nice output for successful results."""
        test_args = ['ag3tools', 'run', 'web_search', '--kv', 'query=test', '--kv', 'max_results=1']

        captured_output = io.StringIO()
        with patch('sys.argv', test_args), patch('sys.stdout', captured_output):
            try:
                main()
            except SystemExit:
                pass  # CLI might exit normally

        output = captured_output.getvalue()
        # Should show formatted results, not raw Python objects
        assert "Found " in output or "Error" in output  # Either success or error format

    def test_run_command_with_error(self):
        """Test that run command shows clean error output."""
        test_args = ['ag3tools', 'run', 'fetch_page', '--kv', 'url=invalid-url']

        captured_output = io.StringIO()
        with patch('sys.argv', test_args), patch('sys.stdout', captured_output):
            try:
                main()
            except SystemExit:
                pass

        output = captured_output.getvalue()
        assert "Error [FETCH_ERROR]:" in output
        assert "Failed to fetch invalid-url" in output

    def test_run_command_with_json_flag(self):
        """Test that --json flag outputs JSON instead of formatted text."""
        test_args = ['ag3tools', 'run', 'web_search', '--kv', 'query=test', '--kv', 'max_results=1', '--json']

        captured_output = io.StringIO()
        with patch('sys.argv', test_args), patch('sys.stdout', captured_output):
            try:
                main()
            except SystemExit:
                pass

        output = captured_output.getvalue()
        # Should be JSON, not formatted text
        if output.strip():  # If there's output
            import json
            try:
                parsed = json.loads(output)
                assert 'success' in parsed
            except json.JSONDecodeError:
                pytest.fail("Output should be valid JSON when --json flag is used")

    def test_docs_command_formatting(self):
        """Test that docs command shows clean URL output."""
        test_args = ['ag3tools', 'docs', 'python']

        captured_output = io.StringIO()
        with patch('sys.argv', test_args), patch('sys.stdout', captured_output):
            try:
                main()
            except SystemExit:
                pass

        output = captured_output.getvalue().strip()
        # Should show just a URL or an error message
        if output:
            assert output.startswith('http') or output.startswith('Error [')


class TestCLIErrorHandling:
    """Test CLI error handling improvements."""

    def test_cli_handles_tool_errors_gracefully(self):
        """Test that CLI doesn't crash on tool errors."""
        test_args = ['ag3tools', 'run', 'fetch_page', '--kv', 'url=']

        captured_output = io.StringIO()
        captured_error = io.StringIO()

        with patch('sys.argv', test_args), \
             patch('sys.stdout', captured_output), \
             patch('sys.stderr', captured_error):
            try:
                main()
            except SystemExit as e:
                # CLI should exit gracefully, not crash
                assert e.code != 1 or "Error [" in captured_output.getvalue()

    def test_cli_shows_helpful_error_for_missing_tool(self):
        """Test CLI behavior when tool doesn't exist."""
        test_args = ['ag3tools', 'run', 'nonexistent_tool']

        captured_output = io.StringIO()
        captured_error = io.StringIO()

        with patch('sys.argv', test_args), \
             patch('sys.stdout', captured_output), \
             patch('sys.stderr', captured_error):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Should exit with error code 1
        assert exc_info.value.code == 1

        # Should show helpful error message
        output = captured_output.getvalue()
        assert "Error: Tool 'nonexistent_tool' not found" in output

    def test_cli_handles_invalid_parameters(self):
        """Test CLI behavior with invalid parameters."""
        test_args = ['ag3tools', 'run', 'web_search', '--kv', 'invalid_param=value']

        captured_output = io.StringIO()
        captured_error = io.StringIO()

        with patch('sys.argv', test_args), \
             patch('sys.stdout', captured_output), \
             patch('sys.stderr', captured_error):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Should exit with error code 1
        assert exc_info.value.code == 1

        # Should show helpful validation error
        output = captured_output.getvalue()
        assert "Error: Invalid parameters for tool 'web_search'" in output
        assert "query" in output  # Should mention the missing required field
