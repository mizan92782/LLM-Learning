# ============================================================
# productAnalyzer/services.py — Product Analyzer business logic
#
# FUNCTIONS:
#   analyzeProduct()  → analyzes a product based on name + description
# ============================================================

import os
from dotenv import load_dotenv
from anthropic import Anthropic

SYSTEM_PROMPT = """
You are an expert product analyst and business consultant.

Your responsibilities:
- Analyze products based on their name and description.
- Identify strengths and weaknesses of the product.
- Suggest target audience and market positioning.
- Recommend improvements and new features.
- Provide competitor comparison insights.
- Give a business viability score out of 10.

Rules:
- Be concise, structured, and data-driven.
- Always respond in the same language the user writes in.
- Ask for clarification if the product description is too vague.

Response format:
1. 📦 Product Overview
2. ✅ Strengths
3. ⚠️  Weaknesses
4. 🎯 Target Audience
5. 💡 Improvement Suggestions
6. 📊 Business Viability Score (out of 10)
"""


def _get_client() -> Anthropic:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing in .env")
    return Anthropic(api_key=api_key)


def _get_model() -> str:
    return os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


# ============================================================
# Analyze a product — returns full analysis at once
# ============================================================
def analyzeProduct(product_name: str, description: str) -> str:
    client = _get_client()

    prompt = f"Product Name: {product_name}\n\nDescription: {description}"

    response = client.messages.create(
        model=_get_model(),
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


# ============================================================
# Analyze a product — returns streaming response
# ============================================================
def analyzeProductStream(product_name: str, description: str):
    client = _get_client()

    prompt = f"Product Name: {product_name}\n\nDescription: {description}"

    with client.messages.stream(
        model=_get_model(),
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            yield text
