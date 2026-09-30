# ============================================================
# main.py — Entry point of the FastAPI application
#
# HOW TO RUN:
#   1. Activate virtual environment:
#        source venv/bin/activate
#
#   2. Start the server:
#        uvicorn main:app --reload
#
#   3. Open API docs in browser:
#        http://127.0.0.1:8000/docs
#
# HOW TO STOP:
#   Press Ctrl + C in the terminal
# ============================================================

from fastapi import FastAPI
from transformers import AutoTokenizer, AutoModel

from apicall.router import router_apicalling
from chatbot.router import router_chatbot
from productAnalyzer.router import router_product
from marketAnalyzer.router import router_market
from tokenTracker.router import router_token
from rag.router import router_rag
from hybridRag.router import router_hybrid_rag

# --- Create FastAPI app ---
app = FastAPI(
    title="LLM API",
    description="Claude AI + BERT API",
    version="1.0.0"
)

# --- Register routers ---
app.include_router(router_apicalling)   # Claude direct API  → /apicalling/...
app.include_router(router_chatbot)      # Chatbot API        → /chatbot/...
app.include_router(router_product)      # Product Analyzer   → /product/...
app.include_router(router_market)       # Market Analyzer    → /market/...
app.include_router(router_token)        # Token Tracker      → /token/...
app.include_router(router_rag)          # RAG                → /rag/...
app.include_router(router_hybrid_rag)   # Hybrid RAG         → /hybrid-rag/...


# --- Root API: BERT embeddings ---
# POST http://127.0.0.1:8000/
# Body: message=<your text>  (query param)
@app.post("/")
def bert_embedding(message: str):
    """Returns BERT last hidden state embeddings for the given text."""
    model_name = "bert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    inputs = tokenizer(message, return_tensors="pt")
    outputs = model(**inputs)
    return {"last_hidden_state": outputs.last_hidden_state.tolist()}
