import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Tuple, Any
from pathlib import Path
from datetime import datetime

from ag3tools.core import settings


@dataclass
class CostEvent:
    ts: float
    tool: str
    model: Optional[str]
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    currency: Optional[str]
    input_cost: Optional[float]
    output_cost: Optional[float]
    total_cost: Optional[float]
    meta: dict
    # New fields for better tracking
    date: Optional[str] = None
    tool_params: Optional[dict] = None
    execution_time_ms: Optional[float] = None


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _get_cost_log_path(date_str: str) -> str:
    """Get the cost log file path for a specific date."""
    # Store in data/cost_logs/ folder in the project
    project_root = Path(__file__).parent.parent.parent
    cost_logs_dir = project_root / "data" / "cost_logs"
    cost_logs_dir.mkdir(parents=True, exist_ok=True)

    return str(cost_logs_dir / f"llm_costs_{date_str}.jsonl")


def _enhance_cost_event(event: CostEvent) -> CostEvent:
    """Add computed fields to the cost event."""
    if event.date is None:
        event.date = datetime.fromtimestamp(event.ts).strftime("%Y-%m-%d")
    return event


def log_cost(event: CostEvent) -> None:
    """Log cost event to both legacy location and new organized structure."""
    if not settings.COST_LOG_ENABLED:
        return

    # Enhance the event with computed fields
    enhanced_event = _enhance_cost_event(event)
    event_dict = asdict(enhanced_event)
    event_json = json.dumps(event_dict, ensure_ascii=False)

    # Log to legacy location for backward compatibility
    _ensure_dir(settings.COST_LOG_PATH)
    with open(settings.COST_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(event_json + "\n")

    # Log to new organized structure (data/cost_logs/llm_costs_YYYY-MM-DD.jsonl)
    date_str = enhanced_event.date or datetime.fromtimestamp(enhanced_event.ts).strftime("%Y-%m-%d")
    new_log_path = _get_cost_log_path(date_str)
    with open(new_log_path, "a", encoding="utf-8") as f:
        f.write(event_json + "\n")


def _parse_cost_value(cost_str: str) -> float:
    """Parse cost string like '$0.00015' to float."""
    if not cost_str or cost_str == '-':
        return 0.0
    return float(cost_str.replace('$', '').replace(',', ''))


def _load_pricing_data() -> Dict[str, Tuple[float, float, str]]:
    """Load pricing data from the extracted LLM costs JSON file."""
    data_dir = Path(__file__).parent.parent.parent / "data"
    costs_file = data_dir / "llm_costs.json"

    if not costs_file.exists():
        # Fallback to hardcoded prices if file doesn't exist
        return {
            "gpt-4o-mini": (0.00000015, 0.00000060, "USD"),
            "gpt-4o": (0.000005, 0.000015, "USD"),
        }

    try:
        with open(costs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        pricing = {}
        for model_data in data.get('models', []):
            if model_data.get('Provider') == 'OpenAI':
                model_name = model_data.get('model')
                if not model_name:
                    continue

                # Get per-100 token pricing (input_price/output_price are per-100 tokens in the data)
                input_cost_str = model_data.get('input_price', '0')
                output_cost_str = model_data.get('output_price', '0')

                try:
                    input_cost = _parse_cost_value(input_cost_str)
                    output_cost = _parse_cost_value(output_cost_str)
                    # Store as per-100 token pricing (will divide by 100 when calculating)
                    pricing[model_name] = (input_cost, output_cost, "USD")
                except (ValueError, TypeError):
                    continue

        return pricing
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        # Fallback to hardcoded prices (per-100 tokens) if parsing fails
        return {
            "gpt-4o-mini": (0.000015, 0.00006, "USD"),
            "gpt-4o": (0.0005, 0.0015, "USD"),
        }


def estimate_openai_cost(model: str, input_tokens: int, output_tokens: int) -> tuple[float, float, float, str]:
    """Estimate cost for OpenAI models using real pricing data.

    Note: Pricing data is stored as per-100 tokens, so we divide by 100 when calculating.
    """
    pricing = _load_pricing_data()

    # Try exact match first
    if model in pricing:
        pin, pout, cur = pricing[model]
    else:
        # Try fallback patterns for common model variants
        fallback_model = None
        if "gpt-4o-mini" in model:
            fallback_model = "gpt-4o-mini"
        elif "gpt-4o" in model:
            fallback_model = "gpt-4o"

        if fallback_model and fallback_model in pricing:
            pin, pout, cur = pricing[fallback_model]
        else:
            # Ultimate fallback to gpt-4o-mini pricing (per-100 tokens)
            pin, pout, cur = pricing.get("gpt-4o-mini", (0.000015, 0.00006, "USD"))

    # Convert from per-100 token pricing to per-token cost
    ic = input_tokens * (pin / 100)
    oc = output_tokens * (pout / 100)
    return ic, oc, ic + oc, cur


def get_tool_cost_stats(tool_name: str, days: int = 30) -> Dict[str, Any]:
    """Get cost statistics for a specific tool over the last N days."""
    from datetime import date, timedelta

    stats = {
        "tool_name": tool_name,
        "total_calls": 0,
        "total_cost": 0.0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "avg_cost_per_call": 0.0,
        "avg_input_tokens": 0.0,
        "avg_output_tokens": 0.0,
        "models_used": {},
        "date_range": f"{days} days"
    }

    # Check cost logs for the last N days
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        log_path = _get_cost_log_path(date_str)

        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            if event.get("tool") == tool_name:
                                stats["total_calls"] += 1
                                stats["total_cost"] += event.get("total_cost", 0) or 0
                                stats["total_input_tokens"] += event.get("input_tokens", 0) or 0
                                stats["total_output_tokens"] += event.get("output_tokens", 0) or 0

                                model = event.get("model", "unknown")
                                if model not in stats["models_used"]:
                                    stats["models_used"][model] = {"calls": 0, "cost": 0.0}
                                stats["models_used"][model]["calls"] += 1
                                stats["models_used"][model]["cost"] += event.get("total_cost", 0) or 0
                        except json.JSONDecodeError:
                            continue
            except (IOError, OSError):
                continue

        current_date += timedelta(days=1)

    # Calculate averages
    if stats["total_calls"] > 0:
        stats["avg_cost_per_call"] = stats["total_cost"] / stats["total_calls"]
        stats["avg_input_tokens"] = stats["total_input_tokens"] / stats["total_calls"]
        stats["avg_output_tokens"] = stats["total_output_tokens"] / stats["total_calls"]

    return stats


def list_recent_tool_usage(days: int = 7) -> Dict[str, Dict[str, Any]]:
    """Get usage statistics for all tools over the last N days."""
    from datetime import date, timedelta

    tool_stats = {}
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        log_path = _get_cost_log_path(date_str)

        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            event = json.loads(line.strip())
                            tool_name = event.get("tool")
                            if not tool_name:
                                continue

                            if tool_name not in tool_stats:
                                tool_stats[tool_name] = {
                                    "calls": 0,
                                    "total_cost": 0.0,
                                    "total_tokens": 0,
                                    "models": set()
                                }

                            tool_stats[tool_name]["calls"] += 1
                            tool_stats[tool_name]["total_cost"] += event.get("total_cost", 0) or 0
                            tool_stats[tool_name]["total_tokens"] += (
                                (event.get("input_tokens", 0) or 0) +
                                (event.get("output_tokens", 0) or 0)
                            )
                            if event.get("model"):
                                tool_stats[tool_name]["models"].add(event["model"])
                        except json.JSONDecodeError:
                            continue
            except (IOError, OSError):
                continue

        current_date += timedelta(days=1)

    # Convert sets to lists for JSON serialization
    for tool_name in tool_stats:
        tool_stats[tool_name]["models"] = list(tool_stats[tool_name]["models"])
        if tool_stats[tool_name]["calls"] > 0:
            tool_stats[tool_name]["avg_cost"] = tool_stats[tool_name]["total_cost"] / tool_stats[tool_name]["calls"]
            tool_stats[tool_name]["avg_tokens"] = tool_stats[tool_name]["total_tokens"] / tool_stats[tool_name]["calls"]
        else:
            tool_stats[tool_name]["avg_cost"] = 0.0
            tool_stats[tool_name]["avg_tokens"] = 0.0

    return tool_stats
