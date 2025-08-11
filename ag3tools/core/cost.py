import json
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional

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


def estimate_openai_cost(model: str, input_tokens: int, output_tokens: int) -> tuple[float, float, float, str]:
    # Prices are placeholders; update as needed from OpenAI pricing
    pricing = {
        "gpt-4o-mini": (0.00000015, 0.00000060, "USD"),  # input, output per token
        "gpt-4o": (0.000005, 0.000015, "USD"),
    }
    pin, pout, cur = pricing.get(model, pricing["gpt-4o-mini"])
    ic = input_tokens * pin
    oc = output_tokens * pout
    return ic, oc, ic + oc, cur
