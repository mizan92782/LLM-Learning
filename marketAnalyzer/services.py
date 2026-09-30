# ============================================================
# marketAnalyzer/services.py — Market Analyzer business logic
#
# FUNCTION:
#   analyzeMarket()       → full analysis at once
#   analyzeMarketStream() → streaming analysis
# ============================================================

import os
from dotenv import load_dotenv
from anthropic import Anthropic

SYSTEM_PROMPT = """
You are an expert market analyst specializing in the Bangladesh (BD) market.

Your responsibilities:
- Analyze company and product pricing data in the Bangladesh market.
- Evaluate whether the average price is competitive in BD.
- Identify market opportunities and risks in Bangladesh.
- Suggest pricing strategies for the BD market.
- Compare with typical BD market standards.

Rules:
- Always consider Bangladesh's economic context (income level, market trends).
- Be concise, structured, and practical.
- Use BDT (Taka) as the currency reference.
- Always respond in the same language the user writes in.

Response format:
1. 🏢 Company Overview
2. 💰 Price Analysis in BD Market
3. 📈 Market Opportunity
4. ⚠️  Market Risks
5. 🎯 Target Customer in BD
6. 💡 Pricing Strategy Recommendation
7. 📊 Market Competitiveness Score (out of 10)
"""


def _get_client() -> Anthropic:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing in .env")
    return Anthropic(api_key=api_key)


def _get_model() -> str:
    return os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


def _build_prompt(company_name, product_name, category, average_price_bd, monthly_sales, target_area, description):
    return f"""
Company Name      : {company_name}
Product Name      : {product_name}
Category          : {category}
Average Price(BDT): {average_price_bd}
Monthly Sales     : {monthly_sales} units
Target Area in BD : {target_area}
Description       : {description}
"""


def analyzeMarket(
    company_name: str,
    product_name: str,
    category: str,
    average_price_bd: float,
    monthly_sales: int,
    target_area: str,
    description: str
) -> str:
    client = _get_client()
    response = client.messages.create(
        model=_get_model(),
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_prompt(
            company_name, product_name, category,
            average_price_bd, monthly_sales, target_area, description
        )}]
    )
    return response.content[0].text


def analyzeMarketStream(
    company_name: str,
    product_name: str,
    category: str,
    average_price_bd: float,
    monthly_sales: int,
    target_area: str,
    description: str
):
    client = _get_client()
    with client.messages.stream(
        model=_get_model(),
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_prompt(
            company_name, product_name, category,
            average_price_bd, monthly_sales, target_area, description
        )}]
    ) as stream:
        for text in stream.text_stream:
            yield text
