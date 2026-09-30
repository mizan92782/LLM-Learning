# ============================================================
# productAnalyzer/router.py — Product Analyzer API routes
#
# ROUTES:
#   POST /product/analyze         → full analysis at once
#   POST /product/analyze/stream  → streaming analysis
#
# EXAMPLE REQUEST BODY:
#   {
#     "product_name": "EcoBottle",
#     "description": "A reusable smart water bottle that tracks hydration."
#   }
# ============================================================

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from productAnalyzer.services import analyzeProduct, analyzeProductStream
from security.guard import validate_input

router_product = APIRouter(prefix="/product", tags=["Product Analyzer"])


class ProductRequest(BaseModel):
    product_name: str
    description: str


# --- Full analysis ---
# POST http://127.0.0.1:8000/product/analyze
@router_product.post("/analyze")
def analyze(request: ProductRequest):
    try:
        validate_input(request.product_name, "product_name")
        validate_input(request.description, "description")
        result = analyzeProduct(request.product_name, request.description)
        return {"analysis": result}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Streaming analysis ---
# POST http://127.0.0.1:8000/product/analyze/stream
@router_product.post("/analyze/stream")
def analyze_stream(request: ProductRequest):
    try:
        validate_input(request.product_name, "product_name")
        validate_input(request.description, "description")
        return StreamingResponse(
            analyzeProductStream(request.product_name, request.description),
            media_type="text/event-stream"
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
