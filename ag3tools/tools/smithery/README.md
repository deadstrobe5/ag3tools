# Smithery MCP Server Integration

Use any [Smithery](https://smithery.ai)-hosted MCP server with ag3tools in just 2 lines of code.

## Quick Start

```python
import ag3tools
from ag3tools.tools.smithery import import_smithery_server

# Import tools from any Smithery server
import_smithery_server(
    "@nickclyde/duckduckgo-mcp-server",
    smithery_api_key="your-smithery-api-key"
)

# Use them like any other ag3tools tool
result = ag3tools.invoke_tool(
    "smithery:@nickclyde/duckduckgo-mcp-server:search",
    query="Python programming"
)
```

## Installation

The Smithery integration requires the MCP SDK and python-dotenv:

```bash
pip install "mcp[cli]" python-dotenv
```

## Configuration

1. Get your free API key at [smithery.ai](https://smithery.ai)
2. Copy `.env.example` to `.env` 
3. Add your API key: `SMITHERY_API_KEY=your-key-here`

The integration automatically loads from `.env` file.

## Available Functions

### Quick Shortcuts

Use pre-configured shortcuts for popular servers:

```python
from ag3tools.tools.smithery import use_duckduckgo, use_exa

# DuckDuckGo - no API key needed for DDG itself
tools = use_duckduckgo()  # Automatically uses SMITHERY_API_KEY from env

# Exa search - requires Exa API key
tools = use_exa(exa_api_key="your-exa-key")
```

### `import_smithery_server`
Import tools from any Smithery-hosted MCP server:

```python
imported_tools = import_smithery_server(
    server_name="@nickclyde/duckduckgo-mcp-server",
    smithery_api_key="your-api-key",  # Or set SMITHERY_API_KEY env var
    prefix="ddg",  # Optional: custom prefix for tool names
    config={}      # Optional: server-specific configuration
)
```

### `list_smithery_tools`
List available tools without importing them.

```python
tools = list_smithery_tools(
    server_name="@nickclyde/duckduckgo-mcp-server",
    smithery_api_key="your-api-key"
)
for tool in tools:
    print(f"{tool['name']}: {tool['description']}")
```

### `get_imported_smithery_tools`
Get a list of all currently imported Smithery tools.

```python
imported = get_imported_smithery_tools()
print(f"Imported tools: {imported}")
```

## Examples

### DuckDuckGo Search (No API key needed for DDG)
```python
# Method 1: Use the shortcut (recommended)
from ag3tools.tools.smithery import use_duckduckgo
use_duckduckgo()  # Auto-loads SMITHERY_API_KEY from env

# Method 2: Standard import
import_smithery_server("@nickclyde/duckduckgo-mcp-server", prefix="ddg")

# Use the tool
result = ag3tools.invoke_tool(
    "ddg:search",
    query="Python tutorials",
    max_results=5
)
```

### Exa Search (Requires Exa API key)
```python
# Method 1: Use the shortcut (recommended)
from ag3tools.tools.smithery import use_exa
use_exa(exa_api_key="your-exa-key")

# Method 2: Standard import
import_smithery_server(
    "exa",
    config={"exaApiKey": "your-exa-api-key"},
    prefix="exa"
)

# Use the tool
result = ag3tools.invoke_tool(
    "exa:web_search_exa",
    query="latest AI news",
    numResults=10
)
```

### Other Servers

Browse available servers at [smithery.ai/servers](https://smithery.ai/servers).

## How It Works

1. The integration connects to Smithery's MCP server hosting platform
2. It discovers available tools from the specified server
3. Tools are dynamically imported into ag3tools with proper type validation
4. You can use them immediately with `ag3tools.invoke_tool()`

## Error Handling

All imported tools return a consistent response format:

```python
{
    "success": True/False,
    "result": <tool_output>,     # When successful
    "error": <error_message>,    # When failed
    "server": <server_name>,     # Server that handled the request
    "tool": <tool_name>          # Tool that was called (on error)
}
```

## Notes

- Tools are imported with a prefix to avoid naming conflicts
- The default prefix is `smithery:{server_name}:`
- Some servers require additional API keys (passed via `config`)
- All imported tools are tagged with `["smithery", "imported", server_name]`
