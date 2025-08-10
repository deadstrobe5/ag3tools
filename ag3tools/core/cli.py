import argparse
import sys
from ag3tools.core.registry import list_tools, invoke_tool


def main() -> None:
    """Unified CLI for ag3tools."""
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
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "list":
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
            import json as _json
            print(_json.dumps(out))
        else:
            for spec in specs:
                suffix = f" [tags: {', '.join(spec.tags)}]" if spec.tags else ""
                print(f"{spec.name}: {spec.description}{suffix}")
    
    elif args.command == "run":
        kwargs = {}
        for pair in args.kv:
            if "=" in pair:
                k, v = pair.split("=", 1)
                kwargs[k] = v
        result = invoke_tool(args.tool, **kwargs)
        if args.json:
            try:
                from pydantic import BaseModel
                if isinstance(result, BaseModel):
                    print(result.model_dump_json())
                else:
                    import json as _json
                    print(_json.dumps(result))
            except Exception:
                print(result)
        else:
            print(result)
    
    elif args.command == "docs":
        tool = "find_docs_validated" if args.validate else "find_docs"
        result = invoke_tool(tool, technology=args.technology)
        if args.json:
            try:
                from pydantic import BaseModel
                if isinstance(result, BaseModel):
                    print(result.model_dump_json())
                else:
                    import json as _json
                    print(_json.dumps(result))
            except Exception:
                print(result)
        else:
            if hasattr(result, 'url') and result.url:
                print(result.url)
            else:
                print("No documentation found")


