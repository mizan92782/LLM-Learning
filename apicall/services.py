# ============================================================
# apicall/services.py — Claude API business logic
#
# FUNCTIONS:
#   apicallingFunction()       → single response (normal)
#   apicallingStreamFunction() → streaming response (chunk by chunk)
# ============================================================

import os
from dotenv import load_dotenv
from anthropic import Anthropic

# --- Shared system prompt ---
SYSTEM_PROMPT = """
You are an experienced Python and Django backend developer.

Your responsibilities:
- Explain Python and Django concepts.
- Help users build REST APIs.
- Debug Python and Django code.
- Suggest clean and maintainable architecture.

Context:
The user is a beginner-to-intermediate backend developer
learning Django REST Framework.

Rules:
- Explain concepts step by step.
- Use simple Bengali.
- Provide practical Python examples.
- Explain the purpose of important code.
- Ask questions if requirements are unclear.

Response format:
1. Concept
2. Explanation
3. Code example
4. Code explanation
5. Best practices
"""


def _get_client() -> Anthropic:
    """Load .env and return Anthropic client."""
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing in .env")
    return Anthropic(api_key=api_key)


def _get_model() -> str:
    return os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


# --- Normal (full) response ---
# Use when you want the complete answer at once
def apicallingFunction(prompt: str) -> str:
    client = _get_client()
    response = client.messages.create(
        model=_get_model(),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


# --- Streaming response ---
# Use when you want to show answer word by word (like ChatGPT typing effect)
def apicallingStreamFunction(prompt: str):
    client = _get_client()
    with client.messages.stream(
        model=_get_model(),
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            yield text
            
            
            
            
            
            


#!============= Create a product analyzer with json retuen==========
def productAnalyzer(product_name: str) -> str:
    client = _get_client()
    prompt = f"""
    Analyze the following product:
    
    Name: {product_name}
    
    
    Provide a detailed analysis including:
    1. Give average price in Bangladesh
    2. Estiamte price in average
    3.where to buy
    """
    
    response = client.messages.create(
        model=_get_model(),
        max_tokens=1024,
        system="You are a product analysis expert. Provide professional, structured analysis.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return _extract_text(response)
    