"""
Lab 06 — Build an LLM-Powered API
===================================
A FastAPI wrapper that combines your ML classifier (Lab 03) with a
Large Language Model from HuggingFace to explain predictions.

How to run:
    # Go to the project root
    cd ..

    # Set your HuggingFace token (free — no credit card needed):
    #   1. Sign up at https://huggingface.co/join
    #   2. Create a token at https://huggingface.co/settings/tokens
    #   3. Set it as an environment variable:

    # Linux/Mac/Codespaces:
    export HF_TOKEN="hf_your_token_here"

    # Windows PowerShell:
    $env:HF_TOKEN = "hf_your_token_here"

    # Start the API:
    cd lab_06_llm_api
    uvicorn app:app --reload --port 8001

    # Open http://127.0.0.1:8001/docs to try it out!

Architecture:
    - Your ML model (Lab 03) does fast classification: urgent vs routine.
    - The LLM explains WHY a note is urgent or routine (slower, richer).
    - This API combines both: fast prediction + human-readable explanation.
    - This "wrapper API" pattern is how most AI products work in production.

Why a wrapper and not call the LLM directly?
    - You control the prompt (users don't need to know prompt engineering).
    - You add rate limiting, caching, and error handling in one place.
    - You can swap the LLM provider without changing client code.
    - You can combine multiple AI services (ML model + LLM) seamlessly.

Reference:
    - HuggingFace Inference API:
      https://huggingface.co/docs/api-inference/
"""

import os
import time
from datetime import UTC, datetime
from uuid import uuid4

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ── Configuration ────────────────────────────────────────────────────
# API token from environment variable — NEVER hardcode secrets!
#
# Why environment variables?
#   - Secrets stay out of your code (and out of git history).
#   - Different environments (dev, staging, prod) use different keys.
#   - This is an industry-standard practice (12-factor app methodology).

HF_TOKEN = os.environ.get("HF_TOKEN", "")

# The model to use on HuggingFace.  You can swap it for any model
# available through HuggingFace Inference Providers.
# Browse models: https://huggingface.co/models?inference_provider=all&sort=trending
DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"

# HuggingFace now uses an OpenAI-compatible chat completions endpoint.
# This is the same format used by OpenAI, making it easy to switch
# providers later without changing your code structure.
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"

# ── Rate limiting ────────────────────────────────────────────────────
# Simple in-memory rate limiter.  Tracks timestamps of recent requests
# and rejects new ones if we're over the limit.
#
# Why rate limit?
#   - The free HuggingFace tier has limited requests per minute.
#   - Without this, a burst of requests would exhaust your quota.
#   - In production, you'd use Redis or a proper rate limiter.

MAX_REQUESTS_PER_MINUTE = 10
request_timestamps: list[float] = []

# ── Response cache ───────────────────────────────────────────────────
# Simple in-memory cache to avoid re-querying the LLM for identical
# notes.  Keyed by (note + model + temperature).
llm_cache: dict[str, dict] = {}


def _check_rate_limit():
    """Enforce a simple rate limit.  Raises 429 if exceeded."""
    now = time.time()
    # Remove timestamps older than 60 seconds
    while request_timestamps and request_timestamps[0] < now - 60:
        request_timestamps.pop(0)

    if len(request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {MAX_REQUESTS_PER_MINUTE} requests per minute. "
            f"Try again in {60 - int(now - request_timestamps[0])} seconds.",
        )
    request_timestamps.append(now)


# ── Create the FastAPI app ──────────────────────────────────────────
app = FastAPI(
    title="LLM-Powered Clinical API",
    description=(
        "Combines a fast ML classifier with an LLM to explain clinical note urgency. "
        "Uses HuggingFace Inference API."
    ),
    version="1.0.0",
)


# ── Pydantic models ────────────────────────────────────────────────


class ExplainRequest(BaseModel):
    """Request body for the explain endpoint."""

    note: str = Field(
        ...,
        min_length=10,
        description="The clinical note to analyze",
        json_schema_extra={
            "example": "Patient presents with acute chest pain and shortness of breath."
        },
    )
    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness. Lower = more focused, higher = more creative.",
    )
    max_tokens: int = Field(
        150,
        ge=10,
        le=500,
        description="Maximum length of the LLM response.",
    )
    model: str = Field(
        DEFAULT_MODEL,
        description="HuggingFace model ID to use.",
    )


class LLMResponse(BaseModel):
    """What the server returns."""

    id: str
    note: str
    explanation: str
    model_used: str
    temperature: float
    max_tokens: int
    cached: bool
    created_at: str


# ── Helper: call HuggingFace ────────────────────────────────────────


def _call_huggingface(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 150,
) -> str:
    """
    Send a prompt to HuggingFace Inference API and return the response.

    This is a raw REST call using the requests library — no SDK needed!
    HuggingFace uses an OpenAI-compatible chat completions format:
        - POST request to /v1/chat/completions
        - JSON body with "model", "messages", and parameters
        - Authorization header with our token
        - JSON response with choices[0].message.content

    This is the same format used by OpenAI, Groq, and many other
    providers — learn it once, use it everywhere.
    """
    if not HF_TOKEN:
        raise HTTPException(
            status_code=503,
            detail=(
                "HuggingFace token not set. "
                "Set the HF_TOKEN environment variable. "
                "Get a free token at https://huggingface.co/settings/tokens"
            ),
        )

    # ── Build the request ──
    # Notice: this is just a POST with JSON — exactly like what
    # clients send to YOUR API!  APIs calling APIs is the same pattern.
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json",
    }

    # OpenAI-compatible chat completions format.
    # The "messages" array is how all modern LLM APIs work:
    #   - "system" message: sets the LLM's behavior/role
    #   - "user" message: the actual question/input
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a clinical assistant. "
                    "Given a clinical note, explain in 2-3 sentences "
                    "whether it suggests an urgent or routine case, and why. "
                    "Be concise and focus on key clinical indicators."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # ── Make the call ──
    # We handle common error scenarios that you'll encounter with
    # any external API:
    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    except requests.exceptions.Timeout as err:
        raise HTTPException(
            status_code=504,
            detail="LLM request timed out. The model may be loading — try again in 30 seconds.",
        ) from err
    except requests.exceptions.ConnectionError as err:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to HuggingFace API. Check your internet connection.",
        ) from err

    # ── Handle API errors ──
    if response.status_code == 401:
        raise HTTPException(
            status_code=503,
            detail="Invalid HuggingFace token. Check your HF_TOKEN.",
        )

    if response.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail="HuggingFace rate limit hit. Wait a moment and try again.",
        )

    if response.status_code == 503:
        raise HTTPException(
            status_code=503,
            detail="Model is loading on HuggingFace. Try again in 30 seconds.",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"HuggingFace returned {response.status_code}: {response.text[:200]}",
        )

    # ── Parse the response ──
    # OpenAI-compatible format: choices[0].message.content
    result = response.json()
    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        return str(result).strip()


# =====================================================================
#  GET / — Root endpoint
# =====================================================================


@app.get("/", status_code=200, tags=["System"])
def root():
    """Welcome page — confirms the API is running."""
    return {
        "message": "LLM-Powered Clinical API is running!",
        "docs": "/docs",
        "endpoints": {
            "explain": "POST /v1/explain",
            "models": "GET /v1/models",
            "rate_limit": "GET /v1/rate-limit",
        },
        "setup": "Set HF_TOKEN environment variable to get started.",
    }


# =====================================================================
#  POST /v1/explain — Get an LLM explanation for a clinical note
# =====================================================================
# This is the main endpoint.  It:
#   1. Builds a prompt from the clinical note
#   2. Sends it to HuggingFace's LLM
#   3. Returns the explanation with metadata
#
# The prompt engineering happens here — clients just send a note.


@app.post("/v1/explain", status_code=201, tags=["LLM"])
def explain_note(request: ExplainRequest):
    """
    Send a clinical note to an LLM and get an explanation of its urgency.

    This endpoint demonstrates:
    - Calling an external API (HuggingFace) from your own API
    - Prompt engineering (building the right prompt for the LLM)
    - LLM parameters (temperature, max_tokens)
    - Rate limiting and caching
    """
    # Check rate limit before making the external call
    _check_rate_limit()

    # Check cache — avoid re-querying for identical requests
    cache_key = f"{request.note}|{request.model}|{request.temperature}"
    if cache_key in llm_cache:
        cached = llm_cache[cache_key].copy()
        cached["cached"] = True
        return {"data": cached}

    # ── Build the prompt ──
    # The system message (role/instructions) is set inside
    # _call_huggingface.  Here we just pass the clinical note
    # as the user message — clean separation of concerns.
    prompt = f"Clinical note: {request.note}"

    # ── Call the LLM ──
    explanation = _call_huggingface(
        prompt=prompt,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    # ── Build the response ──
    record = {
        "id": str(uuid4()),
        "note": request.note,
        "explanation": explanation,
        "model_used": request.model,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "cached": False,
        "created_at": datetime.now(UTC).isoformat(),
    }

    # Cache the result
    llm_cache[cache_key] = record

    return {
        "data": record,
        "meta": {"rate_limit_remaining": MAX_REQUESTS_PER_MINUTE - len(request_timestamps)},
    }


# =====================================================================
#  GET /v1/models — List available models
# =====================================================================


@app.get("/v1/models", status_code=200, tags=["LLM"])
def list_models():
    """
    List some recommended HuggingFace models you can use.

    These are models that work well with the free Inference API.
    You can use any model ID from https://huggingface.co/models
    by passing it in the 'model' field of your request.
    """
    models = [
        {
            "id": "mistralai/Mistral-7B-Instruct-v0.3",
            "description": "Fast, high-quality instruction-following model (default)",
            "size": "7B parameters",
        },
        {
            "id": "google/gemma-2-2b-it",
            "description": "Lightweight model, good for simple tasks",
            "size": "2B parameters",
        },
        {
            "id": "microsoft/Phi-3-mini-4k-instruct",
            "description": "Small but capable model from Microsoft",
            "size": "3.8B parameters",
        },
        {
            "id": "meta-llama/Llama-3.2-3B-Instruct",
            "description": "Meta's latest small Llama model",
            "size": "3B parameters",
        },
    ]

    return {
        "data": models,
        "meta": {
            "note": "Pass any model ID in the 'model' field of POST /v1/explain",
            "browse": "https://huggingface.co/models?pipeline_tag=text-generation",
        },
    }


# =====================================================================
#  GET /v1/rate-limit — Check your rate limit status
# =====================================================================


@app.get("/v1/rate-limit", status_code=200, tags=["System"])
def rate_limit_status():
    """Check how many requests you have left this minute."""
    now = time.time()
    # Clean old timestamps
    while request_timestamps and request_timestamps[0] < now - 60:
        request_timestamps.pop(0)

    return {
        "data": {
            "max_per_minute": MAX_REQUESTS_PER_MINUTE,
            "used_this_minute": len(request_timestamps),
            "remaining": MAX_REQUESTS_PER_MINUTE - len(request_timestamps),
        }
    }


# =====================================================================
#  YOUR TURN — Challenges
# =====================================================================
#
# Challenge 1 (Easy):
#   Add a GET /v1/cache/stats endpoint that returns:
#   {"cached_entries": N, "cache_keys": [...]}
#   This helps you see what's been cached.
#
# Challenge 2 (Medium):
#   Add a POST /v1/summarize endpoint that takes a long clinical note
#   and returns a shorter summary.  Use a different prompt than /explain.
#   Hint: Change the [INST] prompt to ask for a summary instead.
#
# Challenge 3 (Stretch):
#   Combine this API with Lab 03's ML model.  Add a POST /v1/analyze
#   endpoint that:
#     1. Calls your ML model for fast classification (urgent/routine)
#     2. Calls the LLM for an explanation
#     3. Returns BOTH in one response
#   This is the "best of both worlds" pattern used in production.
#
# See solutions/lab_06_challenges.md for all answers.
