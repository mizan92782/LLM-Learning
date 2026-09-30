# ============================================================
# apicall/router.py — Claude API routes
#
# ROUTES:
#   POST /apicalling/chat         → full response at once
#   POST /apicalling/chat/stream  → streaming response (chunk by chunk)
#
# TEST STREAMING (curl):
#   curl -X POST http://127.0.0.1:8000/apicalling/chat/stream \
#     -H "Content-Type: application/json" \
#     -d '{"prompt": "What is Django?"}' \
#     --no-buffer
# ============================================================

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from apicall.services import apicallingFunction, apicallingStreamFunction
from security.guard import validate_input

router_apicalling = APIRouter(prefix="/apicalling", tags=["Claude Direct API"])


class PromptRequest(BaseModel):
    prompt: str


# --- Full response ---
# POST http://127.0.0.1:8000/apicalling/chat
@router_apicalling.post("/chat")
def chat(request: PromptRequest):
    try:
        validate_input(request.prompt, "prompt")
        result = apicallingFunction(request.prompt)
        return {"response": result}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Streaming response ---
# POST http://127.0.0.1:8000/apicalling/chat/stream
@router_apicalling.post("/chat/stream")
def chat_stream(request: PromptRequest):
    try:
        validate_input(request.prompt, "prompt")
        return StreamingResponse(
            apicallingStreamFunction(request.prompt),
            media_type="text/event-stream"
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
