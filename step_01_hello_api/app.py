"""
Step 1 — Hello API
==================
Your first FastAPI server. No ML yet — just understanding the structure.

Run it:
  uvicorn app:app --reload --port 8000

Then open:
  http://localhost:8000          ← "Hello" response
  http://localhost:8000/docs     ← Interactive Swagger UI (FREE documentation!)
  http://localhost:8000/patient/P001  ← Try a URL parameter
"""

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

# ── 1. Create the app ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Hello Medical API",
    description="My first API — understanding the basics before adding ML",
    version="1.0.0",
)


# ── 2. The simplest possible endpoint ─────────────────────────────────────────
@app.get("/")
def root():
    """
    A GET endpoint — caller asks, we return info.
    No input needed, just a heartbeat.
    """
    return {
        "message": "Welcome to the Medical Research API 🏥",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    }


# ── 3. URL parameters — pass data in the URL ───────────────────────────────────
@app.get("/patient/{patient_id}")
def get_patient(patient_id: str):
    """
    URL parameter: the patient_id comes from the URL itself.
    Try: GET /patient/P001
    """
    # Simulated — replace with real DB lookup
    fake_db = {
        "P001": {"name": "Alice", "age": 45, "condition": "hypertension"},
        "P002": {"name": "Bob", "age": 62, "condition": "diabetes"},
    }
    if patient_id in fake_db:
        return {"patient_id": patient_id, "data": fake_db[patient_id]}
    return {"error": f"Patient {patient_id} not found"}, 404


# ── 4. Query parameters — optional filters after the ? ─────────────────────────
@app.get("/search")
def search_notes(keyword: str, limit: int = 5):
    """
    Query parameters come after the ?: /search?keyword=diabetes&limit=3
    'limit' has a default value of 5 — it's optional.
    """
    fake_notes = [
        "Patient presents with type 2 diabetes and fatigue",
        "Diabetes mellitus, well-controlled on metformin",
        "Hypertension noted, diabetes screening recommended",
        "No diabetes, normal blood sugar levels",
        "Post-op diabetes management required",
        "Diabetes follow-up: A1C levels reviewed",
    ]
    matches = [n for n in fake_notes if keyword.lower() in n.lower()]
    return {
        "keyword": keyword,
        "results": matches[:limit],
        "count": len(matches[:limit]),
    }


# ── 5. POST with a body — the ML pattern ──────────────────────────────────────

class ClinicalNote(BaseModel):
    """
    Pydantic model = the shape of data we expect.
    FastAPI validates this automatically — bad data = clear error message.
    """
    note_text: str
    patient_id: str | None = None  # Optional field


@app.post("/analyze")
def analyze_note(note: ClinicalNote):
    """
    POST endpoint — caller sends data in the body (JSON).
    This is the pattern you'll use for ML predictions.

    Try sending:
    {
      "note_text": "Patient has severe chest pain and shortness of breath",
      "patient_id": "P001"
    }
    """
    # Placeholder — in Step 2 we replace this with a real model
    word_count = len(note.note_text.split())
    has_urgent = any(word in note.note_text.lower()
                     for word in ["severe", "emergency", "critical", "urgent"])

    return {
        "received": note.note_text,
        "word_count": word_count,
        "flagged_urgent": has_urgent,
        "note": "🔧 Real ML classification coming in Step 2!",
    }


# ── CHALLENGE: Add your own endpoint below! ────────────────────────────────────
# Ideas:
# - GET /medications/{drug_name}  → return fake drug info
# - POST /icd-code               → accept a description, return a fake ICD code
# Try it and check http://localhost:8000/docs to see it appear automatically!
