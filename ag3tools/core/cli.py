import argparse
import json as _json
import sys
from typing import Any

from ag3tools.core.registry import list_tools, invoke_tool
from ag3tools.core.cost import get_tool_cost_stats, list_recent_tool_usage


def _print_json_result(result: Any) -> None:
    """Helper to print results as JSON."""
    try:
        from pydantic import BaseModel
        if isinstance(result, BaseModel):
            print(result.model_dump_json())
        else:
            print(_json.dumps(result))
    except Exception:
        print(result)


def _print_tool_result(result: Any) -> None:
    """Helper to print tool results in a user-friendly format."""
    if hasattr(result, 'success') and not result.success:
        print(f"Error [{result.error_code}]: {result.error_message}")
        return

    # Handle specific result types nicely
    if hasattr(result, 'results'):  # WebSearchOutput
        if result.results:
            print(f"Found {len(result.results)} results:")
            for i, r in enumerate(result.results[:3], 1):  # Show first 3
                print(f"  {i}. {r.title}")
                print(f"     {r.url}")
            if len(result.results) > 3:
                print(f"     ... and {len(result.results) - 3} more")
        else:
            print("No results found")
    elif hasattr(result, 'url') and hasattr(result, 'status'):  # FetchPageOutput
        print(f"Status: {result.status}")
        print(f"URL: {result.url}")
        if result.content_type:
            print(f"Content-Type: {result.content_type}")
    elif hasattr(result, 'url') and result.url:  # FindDocsOutput
        print(result.url)
    else:
        # Fallback to regular print
        print(result)


def _handle_list_command(args: argparse.Namespace) -> None:
    """Handle the 'list' command."""
    specs = list_tools()
    tags = set(args.tag)

    if tags:
        specs = [s for s in specs if tags.issubset(set(s.tags))]

    if args.json:
        out = [
            {
                "name": s.name,
                "description": s.description,
                "tags": s.tags,
                "parameters": s.input_model.model_json_schema(),
            }
            for s in specs
        ]
        print(_json.dumps(out))
    else:
        for spec in specs:
            suffix = f" [tags: {', '.join(spec.tags)}]" if spec.tags else ""
            print(f"{spec.name}: {spec.description}{suffix}")


def _handle_run_command(args: argparse.Namespace) -> None:
    """Handle the 'run' command."""
    kwargs = {}
    for pair in args.kv:
        if "=" in pair:
            k, v = pair.split("=", 1)
            kwargs[k] = v

    try:
        result = invoke_tool(args.tool, **kwargs)

        if args.json:
            _print_json_result(result)
        else:
            _print_tool_result(result)
    except KeyError:
        print(f"Error: Tool '{args.tool}' not found")
        sys.exit(1)
    except Exception as e:
        if "validation error" in str(e).lower():
            print(f"Error: Invalid parameters for tool '{args.tool}': {e}")
        else:
            print(f"Error: {e}")
        sys.exit(1)


def _handle_docs_command(args: argparse.Namespace) -> None:
    """Handle the 'docs' command."""
    tool = "find_docs_validated" if args.validate else "find_docs"

    try:
        result = invoke_tool(tool, technology=args.technology)

        if args.json:
            _print_json_result(result)
        else:
            _print_tool_result(result)
    except KeyError:
        print(f"Error: Tool '{tool}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def _handle_costs_command(args: argparse.Namespace) -> None:
    """Handle the 'costs' command."""
    if args.tool:
        # Show stats for specific tool
        stats = get_tool_cost_stats(args.tool, args.days)
        if args.json:
            _print_json_result(stats)
        else:
            print(f"Cost Statistics for '{args.tool}' (last {args.days} days):")
            print(f"  Total calls: {stats['total_calls']}")
            print(f"  Total cost: ${stats['total_cost']:.6f}")
            print(f"  Average cost per call: ${stats['avg_cost_per_call']:.6f}")
            print(f"  Average input tokens: {stats['avg_input_tokens']:.1f}")
            print(f"  Average output tokens: {stats['avg_output_tokens']:.1f}")
            if stats['models_used']:
                print("  Models used:")
                for model, model_stats in stats['models_used'].items():
                    print(f"    {model}: {model_stats['calls']} calls, ${model_stats['cost']:.6f}")
    else:
        # Show overview of all tools
        usage = list_recent_tool_usage(args.days)
        if args.json:
            _print_json_result(usage)
        else:
            print(f"Tool Usage Overview (last {args.days} days):")
            sorted_tools = sorted(usage.items(), key=lambda x: x[1]['total_cost'], reverse=True)
            for tool_name, stats in sorted_tools:
                print(f"  {tool_name}: {stats['calls']} calls, ${stats['total_cost']:.6f}, avg {stats['avg_tokens']:.0f} tokens")


def _setup_parser() -> argparse.ArgumentParser:
    """Set up the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(description="ag3tools CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List tools
    list_parser = subparsers.add_parser("list", help="List all available tools")
    list_parser.add_argument("--tag", action="append", default=[], help="Filter by tag (repeatable)")
    list_parser.add_argument("--json", action="store_true", help="Print JSON output with tags")

    # Run tool
    run_parser = subparsers.add_parser("run", help="Run a tool")
    run_parser.add_argument("tool", help="Tool name")
    run_parser.add_argument("--kv", action="append", default=[], help="key=value pairs")
    run_parser.add_argument("--json", action="store_true", help="Print JSON output")

    # Quick find-docs
    docs_parser = subparsers.add_parser("docs", help="Find documentation for a technology")
    docs_parser.add_argument("technology", help="Technology name")
    docs_parser.add_argument("--validate", action="store_true", help="Validate page content")
    docs_parser.add_argument("--json", action="store_true", help="Print JSON output")

    # Cost analytics
    costs_parser = subparsers.add_parser("costs", help="Show LLM cost analytics")
    costs_parser.add_argument("--tool", help="Show stats for specific tool")
    costs_parser.add_argument("--days", type=int, default=30, help="Number of days to analyze (default: 30)")
    costs_parser.add_argument("--json", action="store_true", help="Print JSON output")

    return parser


def main() -> None:
    """Unified CLI for ag3tools."""
    parser = _setup_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Command dispatch
    command_handlers = {
        "list": _handle_list_command,
        "run": _handle_run_command,
        "docs": _handle_docs_command,
        "costs": _handle_costs_command,
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)
