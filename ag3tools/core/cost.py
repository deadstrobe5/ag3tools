import json
import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Tuple
from pathlib import Path

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


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def log_cost(event: CostEvent) -> None:
    if not settings.COST_LOG_ENABLED:
        return
    _ensure_dir(settings.COST_LOG_PATH)
    with open(settings.COST_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")


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

                # Try to get per-token pricing (input_price/output_price)
                input_cost_str = model_data.get('input_price', '0')
                output_cost_str = model_data.get('output_price', '0')

                try:
                    input_cost = _parse_cost_value(input_cost_str)
                    output_cost = _parse_cost_value(output_cost_str)
                    pricing[model_name] = (input_cost, output_cost, "USD")
                except (ValueError, TypeError):
                    continue

        return pricing
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        # Fallback to hardcoded prices if parsing fails
        return {
            "gpt-4o-mini": (0.00000015, 0.00000060, "USD"),
            "gpt-4o": (0.000005, 0.000015, "USD"),
        }


def estimate_openai_cost(model: str, input_tokens: int, output_tokens: int) -> tuple[float, float, float, str]:
    """Estimate cost for OpenAI models using real pricing data."""
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
            # Ultimate fallback to gpt-4o-mini pricing
            pin, pout, cur = pricing.get("gpt-4o-mini", (0.00000015, 0.00000060, "USD"))

    ic = input_tokens * pin
    oc = output_tokens * pout
    return ic, oc, ic + oc, cur
