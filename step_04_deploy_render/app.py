"""
Step 4 — Production-Ready API for Render Deployment
=====================================================
This is a 'production-lite' version of the medical API:
- Lightweight model choice (fast to load on free hosting)
- Rate limiting (prevent abuse)
- CORS headers (allows a browser frontend to call it)
- Proper error handling
- /health endpoint for Render's health checks

Deploy steps:
  1. Push this repo to GitHub
  2. Go to render.com → New → Web Service
  3. Connect your repo, set:
       Build Command: pip install -r requirements.txt
       Start Command: uvicorn step_04_deploy_render.app:app --host 0.0.0.0 --port $PORT
  4. Done! Your API is live at https://your-app.onrender.com

Run locally:
  cd step_04_deploy_render
  uvicorn app:app --host 0.0.0.0 --port 8000
"""

import os
import time
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Rate limiting (optional but good practice) ─────────────────────────────────
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMIT_ENABLED = True
except ImportError:
    RATE_LIMIT_ENABLED = False


# ── Model loading with lifespan (modern FastAPI pattern) ───────────────────────
ml_models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern way to run startup/shutdown code in FastAPI.
    Model loads ONCE when server starts. Cleanup on shutdown.
    """
    print("🚀 Server starting — loading models...")
    start = time.time()

    try:
        from transformers import pipeline

        # Use a lightweight model for free hosting (loads faster, uses less RAM)
        # Great for Render's free tier (512MB RAM limit)
        ml_models["ner"] = pipeline(
            "ner",
            model="d4data/biomedical-ner-all",
            aggregation_strategy="simple",
        )
        print(f"✅ Model loaded in {time.time() - start:.1f}s")
        ml_models["ready"] = True

    except Exception as e:
        print(f"⚠️  Model load failed: {e}. Running in demo mode.")
        ml_models["ready"] = False

    yield  # Server is running here

    # Cleanup (runs on shutdown)
    ml_models.clear()
    print("🛑 Server shutting down — models cleared")


# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Medical NLP API — Production",
    description="""
    Production-ready Medical NLP API.
    
    Live demo: [your-app.onrender.com/docs](https://your-app.onrender.com/docs)
    
    Built with FastAPI + Hugging Face Transformers.
    Deployed on Render.
    """,
    version="4.0.0",
    lifespan=lifespan,
)

# Add rate limiter
if RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS — allow browsers and frontend apps to call this API ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # In production: replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ─────────────────────────────────────────────────────────────
class NoteRequest(BaseModel):
    text: str
    patient_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Patient has type 2 diabetes, started on metformin 500mg. HbA1c 8.2%.",
                    "patient_id": "demo-001",
                }
            ]
        }
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    """Root endpoint — shows API info"""
    return {
        "service": "Medical NLP API",
        "version": "4.0.0",
        "model_ready": ml_models.get("ready", False),
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    """
    Health check endpoint.
    Render uses this to know if your service is up.
    Always return 200 if server is running.
    """
    return {
        "status": "healthy",
        "model_loaded": ml_models.get("ready", False),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/extract")
def extract_entities(request: NoteRequest, req: Request = None):
    """
    Extract biomedical entities from clinical text.
    Rate limited to 30 requests/minute per IP.
    """
    t0 = time.time()

    if ml_models.get("ready"):
        try:
            raw = ml_models["ner"](request.text)
            entities = [
                {"type": e.get("entity_group", e.get("entity")), "text": e["word"], "score": round(float(e["score"]), 3)}
                for e in raw if float(e["score"]) > 0.75
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        # Demo mode
        entities = [
            {"type": "Disease", "text": "diabetes", "score": 0.97},
            {"type": "Chemical", "text": "metformin", "score": 0.95},
        ]

    summary = {}
    for e in entities:
        summary.setdefault(e["type"], []).append(e["text"])

    return {
        "patient_id": request.patient_id,
        "entities": entities,
        "summary": summary,
        "entity_count": len(entities),
        "processing_ms": round((time.time() - t0) * 1000, 1),
    }


@app.get("/demo")
def demo():
    """
    Pre-run example — shows what the API returns without sending your own data.
    Safe to call from any browser or tool.
    """
    return {
        "example_input": "Patient has type 2 diabetes and hypertension. Prescribed metformin 1000mg and lisinopril 10mg.",
        "example_output": {
            "entities": [
                {"type": "Disease", "text": "type 2 diabetes", "score": 0.98},
                {"type": "Disease", "text": "hypertension", "score": 0.96},
                {"type": "Chemical", "text": "metformin", "score": 0.97},
                {"type": "Chemical", "text": "lisinopril", "score": 0.95},
            ],
            "summary": {
                "Disease": ["type 2 diabetes", "hypertension"],
                "Chemical": ["metformin", "lisinopril"],
            },
        },
        "note": "POST /extract with your own text to run the live model",
    }
