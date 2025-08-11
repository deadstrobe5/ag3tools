import argparse
import json as _json
import sys
from typing import Any

from ag3tools.core.registry import list_tools, invoke_tool


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

    result = invoke_tool(args.tool, **kwargs)

    if args.json:
        _print_json_result(result)
    else:
        print(result)


def _handle_docs_command(args: argparse.Namespace) -> None:
    """Handle the 'docs' command."""
    tool = "find_docs_validated" if args.validate else "find_docs"
    result = invoke_tool(tool, technology=args.technology)

    if args.json:
        _print_json_result(result)
    else:
        if hasattr(result, 'url') and result.url:
            print(result.url)
        else:
            print("No documentation found")


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
    }

    handler = command_handlers.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)
