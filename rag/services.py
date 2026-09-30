# ============================================================
# rag/services.py — RAG (Retrieval Augmented Generation)
#
# WHAT IS RAG?
#   RAG = Give Claude your own documents as knowledge base.
#   Instead of Claude guessing, it reads YOUR documents first,
#   then answers based on them.
#
# HOW IT WORKS (step by step):
#
#   STEP 1: Load Document
#           Read text from a .txt or .pdf file
#
#   STEP 2: Chunk
#           Split the document into small pieces (chunks)
#           Why? Because AI models have token limits
#
#   STEP 3: Embed
#           Convert each chunk into a vector (list of numbers)
#           that represents its meaning
#           Tool used: sentence-transformers
#
#   STEP 4: Store in Vector DB
#           Save all vectors into ChromaDB (a local vector database)
#           ChromaDB saves to disk → survives server restart
#
#   STEP 5: Search (Similarity Search)
#           When user asks a question:
#           → Convert question to vector
#           → Find the most similar chunks in ChromaDB
#
#   STEP 6: Generate Answer
#           Send the similar chunks + question to Claude
#           Claude answers based on YOUR document
#
# COMMANDS TO INSTALL:
#   pip install chromadb sentence-transformers pypdf2
# ============================================================

import os
import re
from dotenv import load_dotenv
from anthropic import Anthropic
import chromadb
from chromadb.utils import embedding_functions

# --- Paths ---
BASE_DIR    = os.path.dirname(__file__)
DOCS_DIR    = os.path.join(BASE_DIR, "docs")       # put your .txt/.pdf files here
CHROMA_DIR  = os.path.join(BASE_DIR, "chromadb")   # vector db saved here

# --- ChromaDB collection name ---
COLLECTION_NAME = "rag_documents"

# --- Embedding model (runs locally, no API needed) ---
EMBED_MODEL = "all-MiniLM-L6-v2"

# --- Chunk settings ---
CHUNK_SIZE    = 500   # characters per chunk
CHUNK_OVERLAP = 50    # overlap between chunks to preserve context


# ============================================================
# STEP 1: Load Document
# Reads a .txt or .pdf file and returns raw text
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

    else:
        raise ValueError(f"Unsupported file type: {ext}. Use .txt or .pdf")


# ============================================================
# STEP 2: Chunk Document
# Splits text into overlapping chunks
# ============================================================
def chunk_text(text: str) -> list[str]:
    # Clean extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP  # overlap

    return chunks


# ============================================================
# STEP 3 + 4: Embed and Store in ChromaDB
# Converts chunks to vectors and saves to local vector DB
# ============================================================
def store_document(file_path: str) -> dict:
    # Load
    text = load_document(file_path)

    # Chunk
    chunks = chunk_text(text)

    # Connect to ChromaDB (saved to disk)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Use sentence-transformers for embedding (runs locally)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )

    # Get or create collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn
    )

    # Store each chunk with a unique ID
    file_name = os.path.basename(file_path)
    ids        = [f"{file_name}_chunk_{i}" for i in range(len(chunks))]
    metadatas  = [{"source": file_name, "chunk": i} for i in range(len(chunks))]

    collection.upsert(
        ids=ids,
        documents=chunks,
        metadatas=metadatas
    )

    return {
        "message"         : f"Document '{file_name}' stored successfully.",
        "total_chunks"    : len(chunks),
        "collection"      : COLLECTION_NAME,
        "vector_db_path"  : CHROMA_DIR
    }


# ============================================================
# STEP 5: Similarity Search
# Finds the most relevant chunks for a query
# ============================================================
def search_similar(query: str, top_k: int = 3) -> list[dict]:
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn
    )

    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    # Format results
    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "chunk"     : doc,
            "source"    : results["metadatas"][0][i]["source"],
            "distance"  : round(results["distances"][0][i], 4)
            # distance: lower = more similar
        })

    return chunks


# ============================================================
# STEP 6: RAG — Ask Claude using your documents
# Retrieves relevant chunks then asks Claude
# ============================================================
def ragAnswer(question: str, top_k: int = 3) -> dict:
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing in .env")

    # Step 5: find relevant chunks
    similar_chunks = search_similar(question, top_k)

    if not similar_chunks:
        return {
            "answer"  : "No relevant documents found. Please upload a document first.",
            "sources" : []
        }

    # Build context from chunks
    context = "\n\n".join([f"[{c['source']}]:\n{c['chunk']}" for c in similar_chunks])

    # Step 6: ask Claude with context
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
        "sources" : [{"source": c["source"], "distance": c["distance"]} for c in similar_chunks],
        "token_usage": {
            "input_tokens"  : response.usage.input_tokens,
            "output_tokens" : response.usage.output_tokens,
            "total_tokens"  : response.usage.input_tokens + response.usage.output_tokens
        }
    }
