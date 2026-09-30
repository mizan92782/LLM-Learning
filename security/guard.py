# ============================================================
# security/guard.py — Prompt Injection Protection
#
# HOW TO USE:
#   from security.guard import validate_input
#   validate_input(user_text)   # raises HTTPException if malicious
# ============================================================

import re
from fastapi import HTTPException

# --- Known prompt injection patterns ---
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"forget\s+(all\s+)?(previous|above|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|above|prior)",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an)",
    r"pretend\s+(you\s+are|to\s+be)",
    r"your\s+(new\s+)?role\s+is",
    r"system\s*prompt",
    r"reveal\s+(your\s+)?(instructions|prompt|system)",
    r"print\s+(your\s+)?(instructions|prompt|system)",
    r"what\s+(are\s+)?your\s+instructions",
    r"override\s+(your\s+)?(instructions|rules)",
    r"bypass\s+(your\s+)?(instructions|rules|restrictions)",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"dan\s+mode",
]

# --- Max input length ---
MAX_LENGTH = 2000


def validate_input(text: str, field_name: str = "input"):
    """
    Validates user input against prompt injection attacks.
    Raises HTTPException 400 if malicious content is detected.
    """

    # 1. Check length
    if len(text) > MAX_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} is too long. Max {MAX_LENGTH} characters allowed."
        )

    # 2. Check for injection patterns (case-insensitive)
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid {field_name}: potentially malicious content detected."
            )

    return text
