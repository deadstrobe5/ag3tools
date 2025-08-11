#!/usr/bin/env python3
"""
Cost Analysis Utility for ag3tools

This script provides advanced analytics for LLM tool usage costs.
Run from the project root directory.

Usage:
    python scripts/analyze_costs.py --help
    python scripts/analyze_costs.py --summary
    python scripts/analyze_costs.py --tool validate_docs_llm
    python scripts/analyze_costs.py --trends --days 7
    python scripts/analyze_costs.py --export costs_analysis.csv
"""

import argparse
import json
import csv
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any



def load_cost_data(days: int = 30) -> List[Dict]:
    """Load cost data from the last N days."""
    data_dir = Path(__file__).parent.parent / "data" / "cost_logs"
    all_events = []

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        log_file = data_dir / f"llm_costs_{date_str}.jsonl"

        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            all_events.append(event)
                        except json.JSONDecodeError:
                            continue
            except (IOError, OSError):
                continue

        current_date += timedelta(days=1)

    return all_events


def analyze_summary(events: List[Dict]) -> Dict[str, Any]:
    """Generate overall summary statistics."""
    total_calls = len(events)
    total_cost = sum(event.get('total_cost', 0) or 0 for event in events)
    total_tokens = sum(
        (event.get('input_tokens', 0) or 0) + (event.get('output_tokens', 0) or 0)
        for event in events
    )

    tools = set(event.get('tool') for event in events if event.get('tool'))
    models = set(event.get('model') for event in events if event.get('model'))

    avg_cost_per_call = total_cost / total_calls if total_calls > 0 else 0
    avg_tokens_per_call = total_tokens / total_calls if total_calls > 0 else 0

    return {
        'total_calls': total_calls,
        'total_cost': total_cost,
        'total_tokens': total_tokens,
        'unique_tools': len(tools),
        'unique_models': len(models),
        'avg_cost_per_call': avg_cost_per_call,
        'avg_tokens_per_call': avg_tokens_per_call,
        'tools': list(tools),
        'models': list(models)
    }


def analyze_by_tool(events: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """Analyze costs grouped by tool."""
    tool_stats: Dict[str, Dict[str, Any]] = {}

    for event in events:
        tool = event.get('tool')
        if not tool:
            continue

        if tool not in tool_stats:
            tool_stats[tool] = {
                'calls': 0,
                'total_cost': 0.0,
                'total_input_tokens': 0,
                'total_output_tokens': 0,
                'models': set(),
                'execution_times': [],
                'first_used': None,
                'last_used': None
            }

        stats = tool_stats[tool]
        stats['calls'] += 1
        stats['total_cost'] += event.get('total_cost', 0) or 0
        stats['total_input_tokens'] += event.get('input_tokens', 0) or 0
        stats['total_output_tokens'] += event.get('output_tokens', 0) or 0

        if event.get('model'):
            stats['models'].add(event['model'])

        if event.get('execution_time_ms'):
            stats['execution_times'].append(event['execution_time_ms'])

        timestamp = event.get('ts')
        if timestamp:
            if stats['first_used'] is None or timestamp < stats['first_used']:
                stats['first_used'] = timestamp
            if stats['last_used'] is None or timestamp > stats['last_used']:
                stats['last_used'] = timestamp

    # Calculate averages and convert sets to lists
    for tool, stats in tool_stats.items():
        if stats['calls'] > 0:
            stats['avg_cost'] = stats['total_cost'] / stats['calls']
            stats['avg_input_tokens'] = stats['total_input_tokens'] / stats['calls']
            stats['avg_output_tokens'] = stats['total_output_tokens'] / stats['calls']

            if stats['execution_times']:
                stats['avg_execution_time_ms'] = sum(stats['execution_times']) / len(stats['execution_times'])
                stats['min_execution_time_ms'] = min(stats['execution_times'])
                stats['max_execution_time_ms'] = max(stats['execution_times'])

            if stats['first_used']:
                stats['first_used'] = datetime.fromtimestamp(stats['first_used']).isoformat()
            if stats['last_used']:
                stats['last_used'] = datetime.fromtimestamp(stats['last_used']).isoformat()

        stats['models'] = list(stats['models'])
        del stats['execution_times']  # Remove raw data

    return dict(tool_stats)


def analyze_trends(events: List[Dict], days: int = 7) -> Dict[str, Any]:
    """Analyze usage trends over time."""
    daily_stats: Dict[str, Dict[str, Any]] = {}

    for event in events:
        if not event.get('date'):
            continue

        date_key = event['date']
        if date_key not in daily_stats:
            daily_stats[date_key] = {
                'calls': 0,
                'cost': 0.0,
                'tokens': 0,
                'tools': set()
            }

        daily_stats[date_key]['calls'] += 1
        daily_stats[date_key]['cost'] += event.get('total_cost', 0) or 0
        daily_stats[date_key]['tokens'] += (
            (event.get('input_tokens', 0) or 0) +
            (event.get('output_tokens', 0) or 0)
        )
        if event.get('tool'):
            daily_stats[date_key]['tools'].add(event['tool'])

    # Convert sets to counts and sort by date
    trends = {}
    for date_key, stats in daily_stats.items():
        trends[date_key] = {
            'calls': stats['calls'],
            'cost': stats['cost'],
            'tokens': stats['tokens'],
            'unique_tools': len(stats['tools'])
        }

    return dict(sorted(trends.items()))


def export_to_csv(events: List[Dict], filename: str):
    """Export cost data to CSV."""
    if not events:
        print("No data to export")
        return

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'timestamp', 'date', 'tool', 'model', 'input_tokens', 'output_tokens',
            'total_tokens', 'input_cost', 'output_cost', 'total_cost',
            'execution_time_ms', 'currency'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for event in events:
            row = {
                'timestamp': datetime.fromtimestamp(event.get('ts', 0)).isoformat() if event.get('ts') else '',
                'date': event.get('date', ''),
                'tool': event.get('tool', ''),
                'model': event.get('model', ''),
                'input_tokens': event.get('input_tokens', 0),
                'output_tokens': event.get('output_tokens', 0),
                'total_tokens': (event.get('input_tokens', 0) or 0) + (event.get('output_tokens', 0) or 0),
                'input_cost': event.get('input_cost', 0),
                'output_cost': event.get('output_cost', 0),
                'total_cost': event.get('total_cost', 0),
                'execution_time_ms': event.get('execution_time_ms', ''),
                'currency': event.get('currency', 'USD')
            }
            writer.writerow(row)

    print(f"Data exported to {filename}")


def print_summary(summary: Dict[str, Any]):
    """Print formatted summary."""
    print("\n📊 COST ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Total LLM tool calls: {summary['total_calls']:,}")
    print(f"Total cost: ${summary['total_cost']:.6f}")
    print(f"Total tokens processed: {summary['total_tokens']:,}")
    print(f"Average cost per call: ${summary['avg_cost_per_call']:.6f}")
    print(f"Average tokens per call: {summary['avg_tokens_per_call']:.1f}")
    print(f"\nUnique tools used: {summary['unique_tools']}")
    print(f"Models used: {', '.join(summary['models'])}")


def print_tool_analysis(tool_stats: Dict[str, Dict[str, Any]]):
    """Print formatted tool analysis."""
    print("\n🔧 TOOL-BY-TOOL ANALYSIS")
    print("=" * 50)

    # Sort by total cost descending
    sorted_tools = sorted(tool_stats.items(), key=lambda x: x[1]['total_cost'], reverse=True)

    for tool_name, stats in sorted_tools:
        print(f"\n{tool_name}:")
        print(f"  Calls: {stats['calls']:,}")
        print(f"  Total cost: ${stats['total_cost']:.6f}")
        print(f"  Avg cost per call: ${stats['avg_cost']:.6f}")
        print(f"  Avg input tokens: {stats['avg_input_tokens']:.1f}")
        print(f"  Avg output tokens: {stats['avg_output_tokens']:.1f}")

        if 'avg_execution_time_ms' in stats:
            print(f"  Avg execution time: {stats['avg_execution_time_ms']:.0f}ms")

        print(f"  Models: {', '.join(stats['models'])}")

        if stats['first_used'] and stats['last_used']:
            print(f"  First used: {stats['first_used']}")
            print(f"  Last used: {stats['last_used']}")


def print_trends(trends: Dict[str, Any]):
    """Print formatted trend analysis."""
    print("\n📈 USAGE TRENDS")
    print("=" * 50)

    for date_key, stats in trends.items():
        print(f"{date_key}: {stats['calls']} calls, ${stats['cost']:.6f}, "
              f"{stats['tokens']} tokens, {stats['unique_tools']} tools")


def main():
    parser = argparse.ArgumentParser(description="Analyze ag3tools LLM costs")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")
    parser.add_argument("--summary", action="store_true", help="Show overall summary")
    parser.add_argument("--tools", action="store_true", help="Show tool-by-tool analysis")
    parser.add_argument("--tool", help="Show detailed stats for specific tool")
    parser.add_argument("--trends", action="store_true", help="Show daily usage trends")
    parser.add_argument("--export", help="Export data to CSV file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Load data
    events = load_cost_data(args.days)

    if not events:
        print(f"No cost data found for the last {args.days} days")
        return

    # If no specific flags, show summary by default
    if not any([args.summary, args.tools, args.tool, args.trends, args.export]):
        args.summary = True
        args.tools = True

    if args.summary:
        summary = analyze_summary(events)
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print_summary(summary)

    if args.tools:
        tool_stats = analyze_by_tool(events)
        if args.json:
            print(json.dumps(tool_stats, indent=2))
        else:
            print_tool_analysis(tool_stats)

    if args.tool:
        tool_events = [e for e in events if e.get('tool') == args.tool]
        if tool_events:
            tool_stats = analyze_by_tool(tool_events)
            specific_stats = tool_stats.get(args.tool, {})
            if args.json:
                print(json.dumps(specific_stats, indent=2))
            else:
                print_tool_analysis({args.tool: specific_stats})
        else:
            print(f"No data found for tool: {args.tool}")

    if args.trends:
        trends = analyze_trends(events, args.days)
        if args.json:
            print(json.dumps(trends, indent=2))
        else:
            print_trends(trends)

    if args.export:
        export_to_csv(events, args.export)


if __name__ == "__main__":
    main()
