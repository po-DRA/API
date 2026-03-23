"""
Lab 05 — Production-Ready Deployment App
=========================================
This is the deployment-ready version of the prediction API.  It adds:
  - CORS middleware (so browsers can call the API)
  - Graceful demo mode (works even without a trained model)
  - Health check endpoint (required by most hosting platforms)

Deployment options:
  1. Render:  Push to GitHub → connect repo in Render dashboard
             render.yaml handles build + start automatically
  2. HuggingFace Spaces:  Push to a HF Space → Dockerfile handles it
  3. Docker:  docker build -t rest-api-builder . && docker run -p 7860:7860 rest-api-builder

How to run locally:
    uvicorn lab_05_deploy.app:app --reload --port 7860

Reference:
    - FastAPI docs: https://fastapi.tiangolo.com/
"""

import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

import joblib
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Paths ───────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "urgency_classifier.joblib")
META_PATH = os.path.join(PROJECT_ROOT, "models", "model_meta.json")

# ── Global state ────────────────────────────────────────────────────
model = None
model_meta = None
predictions_db: dict[str, dict] = {}


# ── Lifespan ────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model at startup.  If not available, enter demo mode."""
    global model, model_meta

    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"[OK] Model loaded from {MODEL_PATH}")
    else:
        print("[WARN] Model not found — running in DEMO MODE")
        print("   Predictions will return a placeholder response.")
        print("   To use real predictions, run: python lab_02_train_model/train.py")

    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            model_meta = json.load(f)

    yield

    model = None
    model_meta = None


# ── App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Clinical Urgency Prediction API",
    description=(
        "Predicts whether a clinical note is **urgent** or **routine**. "
        "Built as part of the REST-API-Builder tutorial."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ─────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) controls which websites can
# call your API from a browser.
#
# Without CORS, a React app at http://localhost:3000 would be BLOCKED
# from calling your API at http://localhost:7860 — browsers enforce
# this for security.
#
# In production, replace "*" with your actual frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Which domains can call the API
    allow_credentials=True,
    allow_methods=["*"],  # Which HTTP methods are allowed
    allow_headers=["*"],  # Which headers can be sent
)


# ── Pydantic models ────────────────────────────────────────────────


class PredictionRequest(BaseModel):
    note: str = Field(
        ...,
        min_length=10,
        json_schema_extra={
            "example": "Patient presents with acute chest pain and shortness of breath."
        },
    )


# ── Health check ────────────────────────────────────────────────────
# Every production API needs a health check endpoint.
# Hosting platforms (Render, AWS, k8s) ping this endpoint to know
# if your service is alive.  If it returns non-200, they restart it.


@app.get("/health", status_code=200, tags=["System"])
def health_check():
    """Health check endpoint for hosting platforms."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ── Root endpoint ──────────────────────────────────────────────────


@app.get("/", status_code=200, tags=["System"])
def root():
    """Welcome page with links to docs and endpoints."""
    return {
        "message": "Clinical Urgency Prediction API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "predictions": "/v1/predictions",
            "model_info": "/v1/model/info",
        },
    }


# ── Predictions ─────────────────────────────────────────────────────


@app.post("/v1/predictions", status_code=201, tags=["Predictions"])
def create_prediction(request: PredictionRequest):
    """Classify a clinical note as urgent or routine."""

    pred_id = str(uuid4())

    if model is not None:
        # Real prediction
        prediction = model.predict([request.note])[0]
        probabilities = model.predict_proba([request.note])[0]
        confidence = float(max(probabilities))
    else:
        # Demo mode — return a placeholder so the API is still usable
        prediction = "demo"
        confidence = 0.0

    record = {
        "id": pred_id,
        "note": request.note,
        "prediction": prediction,
        "confidence": round(confidence, 4),
        "created_at": datetime.now(UTC).isoformat(),
    }
    predictions_db[pred_id] = record

    return {
        "data": record,
        "meta": {
            "model_loaded": model is not None,
            "model_version": model_meta.get("trained_at", "unknown") if model_meta else "demo",
        },
    }


@app.get("/v1/predictions", status_code=200, tags=["Predictions"])
def list_predictions(
    prediction: str | None = Query(None, description="Filter by label"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List stored predictions with filtering and pagination."""
    results = list(predictions_db.values())

    if prediction:
        results = [r for r in results if r["prediction"] == prediction]

    total = len(results)
    results = results[offset : offset + limit]

    return {
        "data": results,
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@app.get("/v1/predictions/{prediction_id}", status_code=200, tags=["Predictions"])
def get_prediction(prediction_id: str):
    """Get a specific prediction by ID."""
    if prediction_id not in predictions_db:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {"data": predictions_db[prediction_id]}


@app.delete("/v1/predictions/{prediction_id}", status_code=204, tags=["Predictions"])
def delete_prediction(prediction_id: str):
    """Delete a prediction."""
    if prediction_id not in predictions_db:
        raise HTTPException(status_code=404, detail="Prediction not found")
    del predictions_db[prediction_id]


@app.get("/v1/model/info", status_code=200, tags=["Model"])
def get_model_info():
    """Return model metadata."""
    if model_meta is None:
        return {
            "data": {"status": "demo mode — no model loaded"},
            "meta": {"model_loaded": False},
        }
    return {
        "data": model_meta,
        "meta": {"model_loaded": model is not None},
    }
