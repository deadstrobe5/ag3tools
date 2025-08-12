# Changelog

## [Unreleased]

### Added
- **Smithery MCP Server Integration** - Import and use any MCP server from smithery.ai
  - New module: `ag3tools.tools.smithery` for importing MCP servers
  - `import_smithery_server()` - Import tools from any Smithery-hosted server
  - `list_smithery_tools()` - List available tools without importing
  - `get_imported_smithery_tools()` - Get list of imported Smithery tools
  - Automatic type validation using Pydantic models
  - Support for custom tool prefixes to avoid naming conflicts
  - Built-in error handling with consistent response format

### Changed
- Added `mcp[cli]` dependency for MCP SDK support
- Updated README with Smithery integration examples
- Updated cursor rules with Smithery module documentation

### Security
- Removed hardcoded API keys from code
- API keys now read from environment variables (`SMITHERY_API_KEY`)

### Examples
```python
# Import DuckDuckGo search (no API key needed for DDG)
from ag3tools.tools.smithery import import_smithery_server
import_smithery_server("@nickclyde/duckduckgo-mcp-server")
result = ag3tools.invoke_tool("smithery:@nickclyde/duckduckgo-mcp-server:search", query="Python")

# Import with custom prefix
import_smithery_server("exa", prefix="exa", config={"exaApiKey": "your-key"})
result = ag3tools.invoke_tool("exa:web_search_exa", query="AI news")
```

### Testing
- Added `tests/tools/test_smithery_basic.py` with core integration tests
- Added `examples/smithery_simple.py` demonstrating basic usage
- Tests use DuckDuckGo server to avoid rate limiting issues

### Environment Variables
- `SMITHERY_API_KEY` - Your Smithery platform API key (get at smithery.ai)
- Server-specific API keys passed via `config` parameter

### Supported Servers
Browse available servers at [smithery.ai/servers](https://smithery.ai/servers)