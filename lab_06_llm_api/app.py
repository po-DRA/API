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
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# Load .env file from the project root (if it exists).
# This lets you store API keys in a .env file instead of
# setting environment variables manually every time.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

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
DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

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


DEFAULT_SYSTEM_PROMPT = (
    "You are a clinical assistant. "
    "Given a clinical note, explain in 2-3 sentences "
    "whether it suggests an urgent or routine case, and why. "
    "Be concise and focus on key clinical indicators."
)


def _call_huggingface(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 150,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
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
                "content": system_prompt,
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
    # Each status code gets a clear, actionable error message.
    # This is important when wrapping external APIs — your users
    # shouldn't have to understand HuggingFace's error format.
    if response.status_code == 400:
        # Bad request — usually means the model doesn't support chat
        try:
            error_msg = response.json().get("error", {}).get("message", response.text[:200])
        except (ValueError, AttributeError):
            error_msg = response.text[:200]
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not supported. Try a different model. "
            f"Use GET /v1/models to see available models. Error: {error_msg}",
        )

    if response.status_code == 401:
        raise HTTPException(
            status_code=503,
            detail="Invalid HuggingFace token. Check your HF_TOKEN.",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model}' not found on HuggingFace. "
            f"Check the model ID at https://huggingface.co/{model}",
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
        "playground": "/play",
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
    List chat models available through HuggingFace Inference Providers.

    Fetches the list live from HuggingFace — not hardcoded!
    Falls back to a curated list if the API call fails.
    """
    # Try fetching live from HuggingFace
    try:
        response = requests.get(
            "https://router.huggingface.co/v1/models",
            headers={"Authorization": f"Bearer {HF_TOKEN}"},
            timeout=10,
        )
        if response.status_code == 200:
            all_models = response.json().get("data", [])
            # Filter to chat/instruct models only
            chat_models = [
                {"id": m["id"], "owned_by": m.get("owned_by", "unknown")}
                for m in all_models
                if "instruct" in m["id"].lower() or "chat" in m["id"].lower()
            ]
            return {
                "data": chat_models if chat_models else all_models[:20],
                "meta": {
                    "total": len(chat_models if chat_models else all_models),
                    "source": "live",
                    "note": "Pass any model ID in the 'model' field of POST /v1/explain",
                },
            }
    except (requests.exceptions.RequestException, ValueError):
        pass

    # Fallback: curated list of models known to work
    fallback = [
        {"id": "meta-llama/Llama-3.1-8B-Instruct", "owned_by": "meta-llama"},
        {"id": "meta-llama/Llama-3.2-1B-Instruct", "owned_by": "meta-llama"},
        {"id": "meta-llama/Llama-3.2-3B-Instruct", "owned_by": "meta-llama"},
        {"id": "Qwen/Qwen2.5-7B-Instruct", "owned_by": "Qwen"},
    ]
    return {
        "data": fallback,
        "meta": {
            "total": len(fallback),
            "source": "fallback",
            "note": "Could not fetch live list. These are known working models.",
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
#  GET /play — Interactive Web UI
# =====================================================================


@app.get("/play", response_class=HTMLResponse, tags=["System"])
def play_ui():
    """Interactive web UI to explore the LLM API."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Playground</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f0f4f8; color: #1a202c;
            max-width: 800px; margin: 0 auto; padding: 24px;
        }
        h1 { font-size: 1.6rem; margin-bottom: 4px; }
        .subtitle { color: #718096; margin-bottom: 24px; font-size: 0.95rem; }
        .card {
            background: white; border-radius: 12px; padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px;
        }
        label { display: block; font-weight: 600; margin-bottom: 6px; font-size: 0.9rem; }
        .hint { color: #a0aec0; font-weight: 400; font-size: 0.8rem; }
        textarea {
            width: 100%; padding: 12px; border: 1px solid #e2e8f0;
            border-radius: 8px; font-size: 0.95rem; resize: vertical;
            min-height: 80px; font-family: inherit;
        }
        textarea:focus, select:focus { outline: none; border-color: #4299e1; }
        .controls { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-top: 16px; }
        select, input[type=range] { width: 100%; padding: 8px; border: 1px solid #e2e8f0; border-radius: 8px; }
        select { font-size: 0.9rem; background: white; }
        .range-row { display: flex; align-items: center; gap: 8px; }
        .range-row input { flex: 1; }
        .range-val {
            background: #edf2f7; padding: 4px 10px; border-radius: 6px;
            font-size: 0.85rem; font-weight: 600; min-width: 40px; text-align: center;
        }
        button {
            width: 100%; padding: 14px; background: #4299e1; color: white;
            border: none; border-radius: 8px; font-size: 1rem; font-weight: 600;
            cursor: pointer; margin-top: 20px; transition: background 0.2s;
        }
        button:hover { background: #3182ce; }
        button:disabled { background: #a0aec0; cursor: not-allowed; }
        .result {
            margin-top: 20px; display: none;
        }
        .result-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 12px;
        }
        .result-header h3 { font-size: 1rem; }
        .badge {
            padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;
        }
        .badge-cached { background: #c6f6d5; color: #22543d; }
        .badge-live { background: #bee3f8; color: #2a4365; }
        .explanation {
            background: #f7fafc; border-left: 4px solid #4299e1;
            padding: 16px; border-radius: 0 8px 8px 0;
            line-height: 1.6; white-space: pre-wrap;
        }
        .meta-row {
            display: flex; gap: 16px; margin-top: 12px; flex-wrap: wrap;
        }
        .meta-tag {
            background: #edf2f7; padding: 4px 10px; border-radius: 6px;
            font-size: 0.8rem; color: #4a5568;
        }
        .error { background: #fed7d7; border-left-color: #e53e3e; color: #742a2a; }
        .spinner {
            display: inline-block; width: 16px; height: 16px;
            border: 2px solid #fff; border-top-color: transparent;
            border-radius: 50%; animation: spin 0.6s linear infinite;
            vertical-align: middle; margin-right: 8px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .examples { margin-top: 12px; }
        .example-btn {
            display: inline-block; padding: 6px 12px; margin: 4px;
            background: #edf2f7; border: 1px solid #e2e8f0; border-radius: 6px;
            font-size: 0.8rem; cursor: pointer; transition: background 0.2s;
        }
        .example-btn:hover { background: #e2e8f0; }
    </style>
</head>
<body>
    <h1>LLM Playground</h1>
    <p class="subtitle">Explore the Clinical Urgency LLM API interactively</p>

    <div class="card">
        <label>Clinical Note <span class="hint">— what should the LLM analyze?</span></label>
        <textarea id="note" placeholder="Enter a clinical note...">Patient presents with acute chest pain, ST-elevation on ECG, and elevated troponin levels requiring immediate intervention.</textarea>

        <div class="examples">
            <span class="hint">Try these:</span>
            <span class="example-btn" onclick="setNote('Massive upper GI hemorrhage with hemoglobin dropping to 5.2. Two units of PRBCs transfused. Surgery consulted.')">GI hemorrhage</span>
            <span class="example-btn" onclick="setNote('Routine follow-up for well-controlled type 2 diabetes. HbA1c stable at 6.4. Continue current medications.')">Routine diabetes</span>
            <span class="example-btn" onclick="setNote('Patient found unresponsive with GCS of 3. Emergency intubation performed. CT head shows large subdural hematoma.')">Unresponsive patient</span>
            <span class="example-btn" onclick="setNote('Annual wellness visit. No complaints. Blood pressure 118/76. BMI 23. All screening tests current.')">Wellness visit</span>
        </div>

        <div class="controls">
            <div>
                <label>Model</label>
                <select id="model">
                    <option value="meta-llama/Llama-3.1-8B-Instruct" selected>Llama 3.1 8B (default)</option>
                    <option value="meta-llama/Llama-3.2-1B-Instruct">Llama 3.2 1B (fast)</option>
                    <option value="Qwen/Qwen2.5-7B-Instruct">Qwen 2.5 7B</option>
                    <option value="meta-llama/Llama-3.2-3B-Instruct">Llama 3.2 3B</option>
                </select>
            </div>
            <div>
                <label>Temperature <span class="hint">randomness</span></label>
                <div class="range-row">
                    <input type="range" id="temp" min="0" max="2" step="0.1" value="0.7"
                           oninput="document.getElementById('tempVal').textContent=this.value">
                    <span class="range-val" id="tempVal">0.7</span>
                </div>
            </div>
            <div>
                <label>Max Tokens <span class="hint">response length</span></label>
                <div class="range-row">
                    <input type="range" id="tokens" min="10" max="500" step="10" value="150"
                           oninput="document.getElementById('tokensVal').textContent=this.value">
                    <span class="range-val" id="tokensVal">150</span>
                </div>
            </div>
        </div>

        <button id="btn" onclick="explain()">Analyze Note</button>
    </div>

    <div class="result card" id="result">
        <div class="result-header">
            <h3>LLM Explanation</h3>
            <span class="badge" id="cacheBadge"></span>
        </div>
        <div class="explanation" id="explanation"></div>
        <div class="meta-row" id="metaRow"></div>
    </div>

    <script>
        function setNote(text) {
            document.getElementById('note').value = text;
        }

        async function explain() {
            const btn = document.getElementById('btn');
            const result = document.getElementById('result');
            const note = document.getElementById('note').value.trim();

            if (note.length < 10) {
                alert('Note must be at least 10 characters.');
                return;
            }

            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span>Waiting for LLM...';
            result.style.display = 'none';

            try {
                const res = await fetch('/v1/explain', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        note: note,
                        model: document.getElementById('model').value,
                        temperature: parseFloat(document.getElementById('temp').value),
                        max_tokens: parseInt(document.getElementById('tokens').value),
                    })
                });

                const body = await res.json();

                if (!res.ok) {
                    document.getElementById('explanation').textContent = body.detail || 'Unknown error';
                    document.getElementById('explanation').className = 'explanation error';
                    document.getElementById('cacheBadge').textContent = 'ERROR';
                    document.getElementById('cacheBadge').className = 'badge';
                    document.getElementById('cacheBadge').style.background = '#fed7d7';
                    document.getElementById('cacheBadge').style.color = '#742a2a';
                    document.getElementById('metaRow').innerHTML = '';
                } else {
                    const d = body.data;
                    document.getElementById('explanation').textContent = d.explanation;
                    document.getElementById('explanation').className = 'explanation';

                    const badge = document.getElementById('cacheBadge');
                    if (d.cached) {
                        badge.textContent = 'CACHED';
                        badge.className = 'badge badge-cached';
                    } else {
                        badge.textContent = 'LIVE';
                        badge.className = 'badge badge-live';
                    }

                    document.getElementById('metaRow').innerHTML =
                        '<span class="meta-tag">Model: ' + d.model_used.split('/').pop() + '</span>' +
                        '<span class="meta-tag">Temp: ' + d.temperature + '</span>' +
                        '<span class="meta-tag">Tokens: ' + d.max_tokens + '</span>' +
                        (body.meta ? '<span class="meta-tag">Rate limit left: ' + body.meta.rate_limit_remaining + '</span>' : '');
                }

                result.style.display = 'block';
            } catch (e) {
                alert('Connection error: ' + e.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Analyze Note';
            }
        }
    </script>
</body>
</html>
"""


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
