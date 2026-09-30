# ============================================================
# hybridRag/services.py — Hybrid Search RAG
#
# WHAT IS HYBRID SEARCH?
#   Normal RAG uses only Vector Search (semantic similarity).
#   Hybrid RAG uses TWO search methods and combines them:
#
#   1. Vector Search  → finds chunks by MEANING (semantic)
#                       "what is the price?" also finds "cost is..."
#
#   2. Keyword Search → finds chunks by EXACT WORDS (BM25)
#                       "warranty" finds chunks containing "warranty"
#
#   3. RRF Fusion     → combines both results into one ranked list
#                       RRF = Reciprocal Rank Fusion
#
# WHY HYBRID IS BETTER THAN NORMAL RAG?
#   Vector only  → misses exact keyword matches
#   Keyword only → misses meaning-based matches
#   Hybrid       → gets the best of both worlds
#
# INSTALL:
#   pip install chromadb sentence-transformers pypdf2 rank-bm25
# ============================================================

import os
import re
import json
import math
from dotenv import load_dotenv
from anthropic import Anthropic
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi

# --- Paths ---
BASE_DIR        = os.path.dirname(__file__)
DOCS_DIR        = os.path.join(BASE_DIR, "docs")
CHROMA_DIR      = os.path.join(BASE_DIR, "chromadb")
BM25_INDEX_PATH = os.path.join(BASE_DIR, "bm25_index.json")  # keyword index saved here

# --- Settings ---
COLLECTION_NAME = "hybrid_rag"
EMBED_MODEL     = "all-MiniLM-L6-v2"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50
RRF_K           = 60   # RRF constant (60 is standard)


# ============================================================
# STEP 1: Load Document
# ============================================================
def load_document(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            import PyPDF2
            text = ""
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
        except ImportError:
            raise ImportError("Install PyPDF2: pip install pypdf2")

    raise ValueError(f"Unsupported file type: {ext}. Use .txt or .pdf")


# ============================================================
# STEP 2: Chunk Document
# ============================================================
def chunk_text(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + CHUNK_SIZE]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ============================================================
# STEP 3+4: Store in Vector DB (ChromaDB) + BM25 Index
#
# Two things are stored:
#   a) ChromaDB  → for vector/semantic search
#   b) bm25_index.json → for keyword search (BM25)
# ============================================================
def store_document(file_path: str) -> dict:
    text     = load_document(file_path)
    chunks   = chunk_text(text)
    file_name = os.path.basename(file_path)

    # --- Store in ChromaDB (vector search) ---
    os.makedirs(CHROMA_DIR, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn
    )
    ids       = [f"{file_name}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file_name, "chunk_index": i} for i in range(len(chunks))]
    collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)

    # --- Store BM25 index (keyword search) ---
    # Load existing index if any
    existing = _load_bm25_store()
    for i, chunk in enumerate(chunks):
        existing.append({
            "id"      : f"{file_name}_chunk_{i}",
            "text"    : chunk,
            "source"  : file_name
        })
    _save_bm25_store(existing)

    return {
        "message"      : f"'{file_name}' stored in Vector DB and BM25 index.",
        "total_chunks" : len(chunks),
    }


# ============================================================
# BM25 Index Helpers
# BM25 index is saved as a JSON file on disk
# ============================================================
def _load_bm25_store() -> list:
    if os.path.exists(BM25_INDEX_PATH):
        with open(BM25_INDEX_PATH, "r") as f:
            return json.load(f)
    return []


def _save_bm25_store(data: list):
    with open(BM25_INDEX_PATH, "w") as f:
        json.dump(data, f)


# ============================================================
# STEP 5a: Vector Search
# Finds chunks by semantic meaning using ChromaDB
# ============================================================
def vector_search(query: str, top_k: int = 5) -> list[dict]:
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn
    )
    results = collection.query(query_texts=[query], n_results=top_k)

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "id"       : results["ids"][0][i],
            "chunk"    : doc,
            "source"   : results["metadatas"][0][i]["source"],
            "distance" : round(results["distances"][0][i], 4)
        })
    return chunks


# ============================================================
# STEP 5b: Keyword Search (BM25)
# Finds chunks by exact keyword matching
#
# BM25 = Best Match 25
# It scores each chunk based on:
#   - how many query words appear in the chunk
#   - how rare those words are across all chunks
# ============================================================
def keyword_search(query: str, top_k: int = 5) -> list[dict]:
    store = _load_bm25_store()
    if not store:
        return []

    # Tokenize — split text into words
    corpus     = [item["text"].lower().split() for item in store]
    query_tokens = query.lower().split()

    # Build BM25 index
    bm25   = BM25Okapi(corpus)
    scores = bm25.get_scores(query_tokens)

    # Get top_k results by score
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0:   # only include if there is a match
            results.append({
                "id"     : store[idx]["id"],
                "chunk"  : store[idx]["text"],
                "source" : store[idx]["source"],
                "score"  : round(float(scores[idx]), 4)
            })
    return results


# ============================================================
# STEP 5c: RRF Fusion (Reciprocal Rank Fusion)
#
# Combines vector search results and keyword search results
# into one final ranked list.
#
# HOW RRF WORKS:
#   Each chunk gets a score from both searches.
#   RRF score = 1/(rank + K) for each search list
#   Final score = sum of RRF scores from both lists
#
# Example:
#   Chunk A → rank 1 in vector search  → 1/(1+60) = 0.0164
#   Chunk A → rank 3 in keyword search → 1/(3+60) = 0.0159
#   Chunk A final RRF score = 0.0164 + 0.0159 = 0.0323
#
#   Chunk B → rank 2 in vector search  → 1/(2+60) = 0.0161
#   Chunk B → not in keyword search    → 0
#   Chunk B final RRF score = 0.0161
#
#   Chunk A wins because it appeared in BOTH searches.
# ============================================================
def rrf_fusion(
    vector_results  : list[dict],
    keyword_results : list[dict],
    top_k           : int = 5
) -> list[dict]:

    rrf_scores = {}   # { chunk_id: rrf_score }
    chunk_map  = {}   # { chunk_id: chunk_data }

    # Score from vector search
    for rank, item in enumerate(vector_results):
        cid = item["id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0) + 1 / (rank + 1 + RRF_K)
        chunk_map[cid]  = item

    # Score from keyword search
    for rank, item in enumerate(keyword_results):
        cid = item["id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0) + 1 / (rank + 1 + RRF_K)
        chunk_map[cid]  = item

    # Sort by RRF score (highest first)
    sorted_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)[:top_k]

    return [
        {
            "chunk"     : chunk_map[cid]["chunk"],
            "source"    : chunk_map[cid]["source"],
            "rrf_score" : round(rrf_scores[cid], 6)
        }
        for cid in sorted_ids
    ]


# ============================================================
# STEP 6: Hybrid RAG Answer
# Vector search + Keyword search + RRF + Claude
# ============================================================
def hybridRagAnswer(question: str, top_k: int = 5) -> dict:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing in .env")

    # Run both searches
    v_results = vector_search(question, top_k)
    k_results = keyword_search(question, top_k)

    # Fuse with RRF
    fused = rrf_fusion(v_results, k_results, top_k)

    if not fused:
        return {
            "answer"  : "No relevant documents found. Please upload a document first.",
            "sources" : []
        }

    # Build context
    context = "\n\n".join([f"[{c['source']}]:\n{c['chunk']}" for c in fused])

    # Ask Claude
    client = Anthropic(api_key=api_key)
    model  = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

    prompt = f"""Use the following document excerpts to answer the question.
If the answer is not in the documents, say "I don't know based on the provided documents."

--- DOCUMENTS ---
{context}

--- QUESTION ---
{question}
"""

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system="You are a helpful assistant that answers questions based only on provided documents.",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "answer"  : response.content[0].text,
        "sources" : [{"source": c["source"], "rrf_score": c["rrf_score"]} for c in fused],
        "search_breakdown": {
            "vector_results_count"  : len(v_results),
            "keyword_results_count" : len(k_results),
            "fused_results_count"   : len(fused)
        },
        "token_usage": {
            "input_tokens"  : response.usage.input_tokens,
            "output_tokens" : response.usage.output_tokens,
            "total_tokens"  : response.usage.input_tokens + response.usage.output_tokens
        }
    }
