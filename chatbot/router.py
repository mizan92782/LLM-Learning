# ============================================================
# chatbot/router.py — Chatbot API routes
#
# ROUTES:
#   POST /chatbot/chat            → no memory (fresh every time)
#   POST /chatbot/chat/memory     → memory during server session only
#   POST /chatbot/chat/persistent → memory saved forever (JSON file)
#
# HOW TO USE /chat/memory and /chat/persistent:
#   - Send a "session_id" with every request (e.g. "mizan_001")
#   - Use the SAME session_id to continue the conversation
#   - Use a DIFFERENT session_id to start a new conversation
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel

from chatbot.services import (
    chatbotWithoutMemory,
    chatbotWithMemory,
    chatbotWithPersistentMemory
)
from security.guard import validate_input

router_chatbot = APIRouter(prefix="/chatbot", tags=["Chatbot"])


class ChatRequest(BaseModel):
    question: str


class MemoryChatRequest(BaseModel):
    session_id: str   # unique ID per user/conversation
    question: str


# --- No memory ---
# POST http://127.0.0.1:8000/chatbot/chat
# Body: { "question": "What is a list?" }
@router_chatbot.post("/chat")
def chat_without_memory(request: ChatRequest):
    validate_input(request.question, "question")
    return {"response": chatbotWithoutMemory(request.question)}


# --- In-memory (lost on restart) ---
# POST http://127.0.0.1:8000/chatbot/chat/memory
# Body: { "session_id": "mizan_001", "question": "What is a list?" }
@router_chatbot.post("/chat/memory")
def chat_with_memory(request: MemoryChatRequest):
    validate_input(request.question, "question")
    return {"response": chatbotWithMemory(request.session_id, request.question)}


# --- Persistent memory (saved to file, survives restart) ---
# POST http://127.0.0.1:8000/chatbot/chat/persistent
# Body: { "session_id": "mizan_001", "question": "What is a list?" }
@router_chatbot.post("/chat/persistent")
def chat_with_persistent_memory(request: MemoryChatRequest):
    validate_input(request.question, "question")
    return {"response": chatbotWithPersistentMemory(request.session_id, request.question)}
