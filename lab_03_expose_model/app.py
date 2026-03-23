"""
Lab 03 — Expose the Trained Model as a REST API
================================================
This FastAPI app loads the trained urgency classifier and serves it
as a RESTful prediction service.

How to run:
    # First, make sure you trained the model (Lab 02):
    python lab_02_train_model/train.py

    # Then start this API:
    cd lab_03_expose_model
    uvicorn app:app --reload

    # Open http://127.0.0.1:8000/docs to try it out!

Architecture decisions:
    - Model is loaded ONCE at startup using FastAPI's lifespan context.
      This avoids reloading a 10 MB model on every single request.
    - Predictions are stored in memory with UUIDs so clients can
      retrieve, list, and delete them (full CRUD on predictions).
    - Every response uses a consistent envelope: {data: ..., meta: ...}
    - Endpoints follow REST conventions from Lab 00.

Reference:
    - FastAPI lifespan:
      https://fastapi.tiangolo.com/advanced/events/
"""

import json
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

import joblib
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# ── Paths ───────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "urgency_classifier.joblib")
META_PATH = os.path.join(PROJECT_ROOT, "models", "model_meta.json")

# ── Global state ────────────────────────────────────────────────────
# These are set during startup (see lifespan below).
model = None
model_meta = None

# In-memory store for predictions (dict of UUID → prediction record)
predictions_db: dict[str, dict] = {}


# ── Lifespan: load model once at startup ────────────────────────────
# FastAPI's lifespan context manager runs code BEFORE the first request
# and AFTER the last request.  Perfect for loading/unloading heavy
# resources like ML models.
#
# Why not load in a global variable?
#   - The lifespan pattern is the official FastAPI recommendation.
#   - It makes startup failures explicit and logged.
#   - It gives you a clean place to release resources on shutdown.


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model at startup, release at shutdown."""
    global model, model_meta

    # --- Startup ---
    if os.path.exists(MODEL_PATH):
        model = joblib.load(MODEL_PATH)
        print(f"[OK] Model loaded from {MODEL_PATH}")
    else:
        print(f"[WARN] Model not found at {MODEL_PATH}")
        print("   Run 'python lab_02_train_model/train.py' first.")
        print("   The API will start but prediction endpoints won't work.")

    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            model_meta = json.load(f)

    yield  # ← the app runs here

    # --- Shutdown ---
    print("[SHUTDOWN] Releasing model from memory")
    model = None
    model_meta = None


# ── Create the FastAPI app ──────────────────────────────────────────
app = FastAPI(
    title="Clinical Urgency Prediction API",
    description="Predicts whether a clinical note is urgent or routine",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Pydantic models ────────────────────────────────────────────────


class PredictionRequest(BaseModel):
    """What the client sends to request a prediction."""

    note: str = Field(
        ...,
        min_length=10,
        description="The clinical note to classify",
        json_schema_extra={
            "example": "Patient presents with acute chest pain and shortness of breath."
        },
    )


class PredictionResponse(BaseModel):
    """What the server returns for a single prediction."""

    id: str
    note: str
    prediction: str
    confidence: float
    created_at: str


# ── Helper ──────────────────────────────────────────────────────────


def _require_model():
    """Raise 503 if the model is not loaded."""
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run 'python lab_02_train_model/train.py' first.",
        )


# =====================================================================
#  POST /v1/predictions — Create a new prediction
# =====================================================================
# POST because we are CREATING a new resource (the prediction record).
# Returns 201 Created with the prediction in the body.


@app.post("/v1/predictions", status_code=201, tags=["Predictions"])
def create_prediction(request: PredictionRequest):
    """
    Classify a clinical note as urgent or routine.

    REST notes:
    - POST creates a new prediction resource (assigned a UUID).
    - Returns 201 Created because a new resource was stored.
    - Returns 503 if the model is not available.
    """
    _require_model()

    # Get the prediction and confidence
    prediction = model.predict([request.note])[0]
    probabilities = model.predict_proba([request.note])[0]
    confidence = float(max(probabilities))

    # Store the prediction with a UUID
    pred_id = str(uuid4())
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
            "model_version": model_meta.get("trained_at", "unknown") if model_meta else "unknown"
        },
    }


# =====================================================================
#  GET /v1/predictions — List all predictions (with filtering & pagination)
# =====================================================================


@app.get("/v1/predictions", status_code=200, tags=["Predictions"])
def list_predictions(
    prediction: str | None = Query(
        None,
        description="Filter by prediction label (urgent or routine)",
    ),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Results to skip"),
):
    """
    List stored predictions with optional filtering and pagination.

    REST notes:
    - GET for reading, query params for filtering/pagination.
    - This endpoint works even if the model is not loaded (you can
      still browse old predictions).
    """
    results = list(predictions_db.values())

    # Filter by prediction label if requested
    if prediction:
        results = [r for r in results if r["prediction"] == prediction]

    total = len(results)
    results = results[offset : offset + limit]

    return {
        "data": results,
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


# =====================================================================
#  GET /v1/predictions/{prediction_id} — Get one prediction
# =====================================================================


@app.get("/v1/predictions/{prediction_id}", status_code=200, tags=["Predictions"])
def get_prediction(prediction_id: str):
    """
    Retrieve a specific prediction by its ID.

    REST notes:
    - Path parameter identifies the specific resource.
    - Returns 404 if not found.
    """
    if prediction_id not in predictions_db:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {"data": predictions_db[prediction_id]}


# =====================================================================
#  DELETE /v1/predictions/{prediction_id} — Delete a prediction
# =====================================================================


@app.delete("/v1/predictions/{prediction_id}", status_code=204, tags=["Predictions"])
def delete_prediction(prediction_id: str):
    """
    Delete a stored prediction.

    REST notes:
    - Returns 204 No Content on success.
    - Returns 404 if the prediction doesn't exist.
    """
    if prediction_id not in predictions_db:
        raise HTTPException(status_code=404, detail="Prediction not found")
    del predictions_db[prediction_id]


# =====================================================================
#  GET /v1/model/info — Model metadata
# =====================================================================


@app.get("/v1/model/info", status_code=200, tags=["Model"])
def get_model_info():
    """
    Return metadata about the loaded model.

    REST notes:
    - This is a read-only informational endpoint.
    - Returns 503 if no model metadata is available.
    """
    if model_meta is None:
        raise HTTPException(
            status_code=503,
            detail="Model metadata not available.",
        )
    return {
        "data": model_meta,
        "meta": {"model_loaded": model is not None},
    }


# =====================================================================
#  🎯 YOUR TURN — Challenges
# =====================================================================
#
# Challenge 1 (Easy):
#   Add a root / endpoint so visitors see a welcome message instead
#   of 404. Also add GET /v1/predictions/stats that returns:
#   {"total": N, "urgent": N, "routine": N}
#   Hint: Place /stats BEFORE /{prediction_id} in your code!
#
# Challenge 2 (Medium):
#   Add a min_confidence query parameter to the list endpoint
#   so clients can filter for high-confidence predictions only:
#   GET /v1/predictions?min_confidence=0.9
#
# Challenge 3 (Stretch):
#   Add a POST /v1/predictions/batch endpoint that accepts a list
#   of notes and returns predictions for all of them in one call.
#   This is a common pattern for ML APIs — it reduces network
#   round-trips when you have many items to classify.
#
# See solutions/lab_03_challenges.md for all answers.
