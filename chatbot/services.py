# ============================================================
# chatbot/services.py — Chatbot business logic
#
# FUNCTIONS:
#   chatbotWithoutMemory()        → no memory, fresh every time
#   chatbotWithMemory()           → remembers during server session only
#                                   (lost when server restarts)
#   chatbotWithPersistentMemory() → remembers forever (saved to JSON file)
#                                   (survives server restart)
#
# SESSION FILES LOCATION:
#   chatbot/sessions/<session_id>.json
# ============================================================

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

SYSTEM_PROMPT = "You are a helpful Python instructor. Explain simply."

# In-memory store — lost on server restart
# Structure: { "session_id": [ {role, content}, ... ] }
conversation_store: dict = {}

# Folder where persistent session JSON files are saved
SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")


def _get_client() -> Anthropic:
    """Load .env and return Anthropic client."""
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing in .env")
    return Anthropic(api_key=api_key)


def _get_model() -> str:
    return os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


def _extract_text(response) -> str:
    return "\n".join(block.text for block in response.content if block.type == "text")


# ---- Helper: load session from JSON file ----
def _load_session(session_id: str) -> list:
    os.makedirs(SESSION_DIR, exist_ok=True)
    path = os.path.join(SESSION_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []


# ---- Helper: save session to JSON file ----
def _save_session(session_id: str, history: list):
    path = os.path.join(SESSION_DIR, f"{session_id}.json")
    with open(path, "w") as f:
        json.dump(history, f)


# ============================================================
# 1. WITHOUT MEMORY
#    Every question is treated as a brand new conversation.
#    Claude has no idea what you asked before.
# ============================================================
def chatbotWithoutMemory(question: str) -> str:
    client = _get_client()
    response = client.messages.create(
        model=_get_model(),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}]
    )
    return _extract_text(response)


# ============================================================
# 2. WITH MEMORY (in-memory)
#    Claude remembers the conversation using session_id.
#    ⚠️ Memory is lost when the server restarts.
# ============================================================
def chatbotWithMemory(session_id: str, question: str) -> str:
    client = _get_client()

    history = conversation_store.setdefault(session_id, [])
    history.append({"role": "user", "content": question})

    response = client.messages.create(
        model=_get_model(),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history
    )

    answer = _extract_text(response)
    history.append({"role": "assistant", "content": answer})
    return answer


# ============================================================
# 3. WITH PERSISTENT MEMORY (saved to JSON file)
#    Claude remembers the conversation forever.
#    ✅ Memory survives server restarts.
#    Each session is saved in: chatbot/sessions/<session_id>.json
# ============================================================
def chatbotWithPersistentMemory(session_id: str, question: str) -> str:
    client = _get_client()

    history = _load_session(session_id)
    history.append({"role": "user", "content": question})

    response = client.messages.create(
        model=_get_model(),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history
    )

    answer = _extract_text(response)
    history.append({"role": "assistant", "content": answer})
    _save_session(session_id, history)
    return answer

    
    
    
    
    
    #!============= Create a product analyzer with json retuen==========
    def productAnalyzer(product_name: str, features: list, price: float) -> str:
        client = _get_client()
        prompt = f"""
        Analyze the following product:
        
        Name: {product_name}
        Features: {', '.join(features)}
        Price: ${price}
        
        Provide a detailed analysis including:
        1. Market positioning
        2. Target audience
        3. Strengths and weaknesses
        4. Pricing strategy assessment
        """
        
        response = client.messages.create(
            model=_get_model(),
            max_tokens=1024,
            system="You are a product analysis expert. Provide professional, structured analysis.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return _extract_text(response)
        