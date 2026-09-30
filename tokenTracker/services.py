# ============================================================
# tokenTracker/services.py — Token Usage Tracker
#
# FUNCTION:
#   trackTokenUsage() → sends prompt to Claude and returns
#                       response + input/output token usage + cost
# ============================================================

import os
from dotenv import load_dotenv
from anthropic import Anthropic

SYSTEM_PROMPT = "You are a helpful assistant."

# --- Pricing per 1M tokens (USD) ---
PRICING = {
    "claude-sonnet-4-5"         : {"input": 3.00,  "output": 15.00},
    "claude-opus-4-5"           : {"input": 15.00, "output": 75.00},
    "claude-haiku-3-5"          : {"input": 0.80,  "output": 4.00},
}


def _get_client() -> Anthropic:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing in .env")
    return Anthropic(api_key=api_key)


def _get_model() -> str:
    return os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


def trackTokenUsage(prompt: str) -> dict:
    client = _get_client()
    model = _get_model()

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.content[0].text
    input_tokens  = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    total_tokens  = input_tokens + output_tokens

    # --- Calculate cost ---
    price         = PRICING.get(model, {"input": 3.00, "output": 15.00})
    input_cost    = (input_tokens  / 1_000_000) * price["input"]
    output_cost   = (output_tokens / 1_000_000) * price["output"]
    total_cost    = input_cost + output_cost

    return {
        "response"   : answer,
        "model"      : model,
        "token_usage": {
            "input_tokens"  : input_tokens,
            "output_tokens" : output_tokens,
            "total_tokens"  : total_tokens,
        },
        "cost_usd": {
            "input_cost"    : round(input_cost,  8),
            "output_cost"   : round(output_cost, 8),
            "total_cost"    : round(total_cost,  8),
        }
    }
