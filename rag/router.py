# ============================================================
# rag/router.py — RAG API routes
#
# ROUTES:
#   POST /rag/upload    → upload .txt or .pdf → store in vector DB
#   GET  /rag/search    → search similar chunks by query
#   POST /rag/ask       → ask Claude using your documents
#
# HOW TO USE (in order):
#   1. Upload a document first  → POST /rag/upload
#   2. Ask a question           → POST /rag/ask
#   (optional) Search raw chunks→ GET  /rag/search?query=...&top_k=3
# ============================================================

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import os, shutil

from rag.services import store_document, search_similar, ragAnswer
from security.guard import validate_input

router_rag = APIRouter(prefix="/rag", tags=["RAG"])

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")


class QuestionRequest(BaseModel):
    question: str
    top_k: int = 3  # how many chunks to retrieve


# ============================================================
# STEP 1+2+3+4: Upload and store document in vector DB
# POST http://127.0.0.1:8000/rag/upload
# Form: file = your .txt or .pdf file
# ============================================================
@router_rag.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Save uploaded file to docs folder
        os.makedirs(DOCS_DIR, exist_ok=True)
        file_path = os.path.join(DOCS_DIR, file.filename)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Store in vector DB
        result = store_document(file_path)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# STEP 5: Similarity Search (raw chunks)
# GET http://127.0.0.1:8000/rag/search?query=what is python&top_k=3
# ============================================================
@router_rag.get("/search")
def similarity_search(query: str, top_k: int = 3):
    try:
        validate_input(query, "query")
        results = search_similar(query, top_k)
        return {
            "query"   : query,
            "results" : results
            # distance: lower value = more similar to your query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# STEP 6: Ask Claude using your documents
# POST http://127.0.0.1:8000/rag/ask
# Body: { "question": "What is ...?", "top_k": 3 }
# ============================================================
@router_rag.post("/ask")
def ask(request: QuestionRequest):
    try:
        validate_input(request.question, "question")
        result = ragAnswer(request.question, request.top_k)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
