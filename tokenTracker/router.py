# ============================================================
# tokenTracker/router.py — Token Usage API route
#
# ROUTES:
#   POST /token/usage → returns response + token usage
#
# EXAMPLE REQUEST:
#   { "prompt": "What is Python?" }
#
# EXAMPLE RESPONSE:
#   {
#     "response": "Python is ...",
#     "token_usage": {
#       "input_tokens": 23,
#       "output_tokens": 120,
#       "total_tokens": 143
#     }
#   }
# ============================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from tokenTracker.services import trackTokenUsage
from security.guard import validate_input

router_token = APIRouter(prefix="/token", tags=["Token Tracker"])


class TokenRequest(BaseModel):
    prompt: str


# POST http://127.0.0.1:8000/token/usage
@router_token.post("/usage")
def token_usage(request: TokenRequest):
    try:
        validate_input(request.prompt, "prompt")
        result = trackTokenUsage(request.prompt)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
