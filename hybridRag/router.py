# ============================================================
# hybridRag/router.py — Hybrid Search RAG API routes
#
# ROUTES:
#   POST /hybrid-rag/upload          → upload doc to vector DB + BM25 index
#   GET  /hybrid-rag/search/vector   → vector (semantic) search only
#   GET  /hybrid-rag/search/keyword  → keyword (BM25) search only
#   GET  /hybrid-rag/search/hybrid   → both searches fused with RRF
#   POST /hybrid-rag/ask             → hybrid search + Claude answer
#
# HOW TO USE (in order):
#   1. POST /hybrid-rag/upload  → upload your document
#   2. POST /hybrid-rag/ask     → ask your question
# ============================================================

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import os, shutil

from hybridRag.services import (
    store_document,
    vector_search,
    keyword_search,
    rrf_fusion,
    hybridRagAnswer
)
from security.guard import validate_input

router_hybrid_rag = APIRouter(prefix="/hybrid-rag", tags=["Hybrid RAG"])

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")


class QuestionRequest(BaseModel):
    question : str
    top_k    : int = 5


# --- Upload document ---
# POST http://127.0.0.1:8000/hybrid-rag/upload
@router_hybrid_rag.post("/upload")
async def upload(file: UploadFile = File(...)):
    try:
        os.makedirs(DOCS_DIR, exist_ok=True)
        file_path = os.path.join(DOCS_DIR, file.filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return store_document(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Vector search only ---
# GET http://127.0.0.1:8000/hybrid-rag/search/vector?query=...&top_k=5
@router_hybrid_rag.get("/search/vector")
def search_vector(query: str, top_k: int = 5):
    try:
        validate_input(query, "query")
        results = vector_search(query, top_k)
        return {"query": query, "method": "vector", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Keyword search only ---
# GET http://127.0.0.1:8000/hybrid-rag/search/keyword?query=...&top_k=5
@router_hybrid_rag.get("/search/keyword")
def search_keyword(query: str, top_k: int = 5):
    try:
        validate_input(query, "query")
        results = keyword_search(query, top_k)
        return {"query": query, "method": "keyword (BM25)", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Hybrid search (RRF fused) ---
# GET http://127.0.0.1:8000/hybrid-rag/search/hybrid?query=...&top_k=5
@router_hybrid_rag.get("/search/hybrid")
def search_hybrid(query: str, top_k: int = 5):
    try:
        validate_input(query, "query")
        v_results = vector_search(query, top_k)
        k_results = keyword_search(query, top_k)
        fused     = rrf_fusion(v_results, k_results, top_k)
        return {
            "query"   : query,
            "method"  : "hybrid (vector + keyword + RRF)",
            "results" : fused
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Ask Claude using hybrid search ---
# POST http://127.0.0.1:8000/hybrid-rag/ask
@router_hybrid_rag.post("/ask")
def ask(request: QuestionRequest):
    try:
        validate_input(request.question, "question")
        return hybridRagAnswer(request.question, request.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
