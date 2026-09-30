# ============================================================
# marketAnalyzer/router.py — Market Analyzer API routes
#
# ROUTES:
#   POST /market/analyze         → full analysis at once
#   POST /market/analyze/stream  → streaming analysis
#
# EXAMPLE REQUEST BODY:
#   {
#     "company_name": "ACI Limited",
#     "product_name": "ACI Pure Salt",
#     "category": "Food & Beverage",
#     "average_price_bd": 35.0,
#     "monthly_sales": 15000,
#     "target_area": "Dhaka, Chittagong",
#     "description": "Iodized pure salt for household use."
#   }
# ============================================================

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from marketAnalyzer.services import analyzeMarket, analyzeMarketStream
from security.guard import validate_input

router_market = APIRouter(prefix="/market", tags=["Market Analyzer"])


class MarketRequest(BaseModel):
    company_name: str
    product_name: str
    category: str
    average_price_bd: float
    monthly_sales: int
    target_area: str
    description: str


# --- Full analysis ---
# POST http://127.0.0.1:8000/market/analyze
@router_market.post("/analyze")
def market_analyze(request: MarketRequest):
    try:
        validate_input(request.company_name, "company_name")
        validate_input(request.description, "description")
        result = analyzeMarket(
            request.company_name,
            request.product_name,
            request.category,
            request.average_price_bd,
            request.monthly_sales,
            request.target_area,
            request.description
        )
        return {"analysis": result}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Streaming analysis ---
# POST http://127.0.0.1:8000/market/analyze/stream
@router_market.post("/analyze/stream")
def market_analyze_stream(request: MarketRequest):
    try:
        validate_input(request.company_name, "company_name")
        validate_input(request.description, "description")
        return StreamingResponse(
            analyzeMarketStream(
                request.company_name,
                request.product_name,
                request.category,
                request.average_price_bd,
                request.monthly_sales,
                request.target_area,
                request.description
            ),
            media_type="text/event-stream"
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
