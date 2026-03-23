"""
Step 2 — Real Medical NLP API
==============================
We load a Hugging Face model ONCE at startup, then reuse it for every request.
This answers the question: "Does the model run live, or use pre-existing results?"

Answer: IT RUNS LIVE — but the model is loaded into memory only once.
Each request calls the already-loaded model. Very fast after the first load!

Model used: d4data/biomedical-ner-all
A Named Entity Recognition model trained on biomedical text.
It finds: Disease, Drug, Chemical, Gene, Protein mentions in text.

Run it:
  cd step_02_medical_api
  uvicorn app:app --reload --port 8000

First request is slow (model downloads ~500MB on first run).
Every request after that is fast.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import time
import os

# ── Load the model ONCE at startup ────────────────────────────────────────────
# This is the key architectural decision:
# ✅ Load once → serve thousands of requests without reloading
# ❌ Load per request → 30 second wait on every single call (unusable!)

print("⏳ Loading biomedical NLP model... (first time downloads ~500MB)")
start = time.time()

try:
    from transformers import pipeline

    # Named Entity Recognition model fine-tuned on biomedical text
    # Finds: Disease, Drug, Chemical, Gene, Species, etc.
    ner_pipeline = pipeline(
        "ner",
        model="d4data/biomedical-ner-all",
        aggregation_strategy="simple",   # Merges tokens into full words
    )

    # Also load a zero-shot classifier for urgency detection
    # This model can classify text into ANY labels you define — no fine-tuning!
    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
    )

    MODEL_LOADED = True
    print(f"✅ Models loaded in {time.time() - start:.1f}s")

except Exception as e:
    print(f"⚠️  Could not load model: {e}")
    print("Running in DEMO MODE with fake results.")
    MODEL_LOADED = False


# ── App definition ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Medical NLP API",
    description="""
    A real-time NLP API for clinical text analysis.
    
    Powered by Hugging Face transformer models:
    - **NER**: Extracts diseases, drugs, genes from clinical notes
    - **Urgency Classification**: Triage helper using zero-shot classification
    
    The model loads once at startup and runs live on each request.
    """,
    version="2.0.0",
)


# ── Request / Response models ─────────────────────────────────────────────────
class ClinicalNote(BaseModel):
    text: str
    patient_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Patient presents with acute myocardial infarction. "
                            "Currently on aspirin 100mg and metoprolol. "
                            "History of BRCA1 mutation.",
                    "patient_id": "P001"
                }
            ]
        }
    }


class EntityResult(BaseModel):
    entity_type: str
    text: str
    confidence: float


class NERResponse(BaseModel):
    patient_id: Optional[str]
    entities: list[EntityResult]
    entity_summary: dict
    processing_time_ms: float
    model_used: str


class UrgencyResponse(BaseModel):
    text: str
    urgency_level: str
    confidence: float
    all_scores: dict


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "Medical NLP API",
        "model_loaded": MODEL_LOADED,
        "endpoints": ["/extract-entities", "/classify-urgency", "/analyze-full"],
        "docs": "/docs",
    }


@app.get("/health")
def health():
    """Health check — useful for deployment monitoring"""
    return {"status": "healthy", "model_loaded": MODEL_LOADED}


@app.post("/extract-entities", response_model=NERResponse)
def extract_entities(note: ClinicalNote):
    """
    Extract biomedical named entities from clinical text.
    
    Finds: Disease, Drug, Chemical, Gene, Protein, Species mentions.
    Uses Hugging Face NER model running live on each request.
    """
    t0 = time.time()

    if MODEL_LOADED:
        try:
            raw_entities = ner_pipeline(note.text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")
    else:
        # Demo mode — return fake entities so you can test the API structure
        raw_entities = [
            {"entity_group": "Disease", "word": "myocardial infarction", "score": 0.98},
            {"entity_group": "Chemical", "word": "aspirin", "score": 0.95},
            {"entity_group": "Gene", "word": "BRCA1", "score": 0.92},
        ]

    # Clean and structure the results
    entities = [
        EntityResult(
            entity_type=e.get("entity_group", e.get("entity", "UNKNOWN")),
            text=e["word"],
            confidence=round(float(e["score"]), 3),
        )
        for e in raw_entities
        if float(e["score"]) > 0.7  # Filter low-confidence results
    ]

    # Summarize by type
    summary = {}
    for ent in entities:
        summary.setdefault(ent.entity_type, []).append(ent.text)

    return NERResponse(
        patient_id=note.patient_id,
        entities=entities,
        entity_summary=summary,
        processing_time_ms=round((time.time() - t0) * 1000, 1),
        model_used="d4data/biomedical-ner-all" if MODEL_LOADED else "demo-mode",
    )


@app.post("/classify-urgency", response_model=UrgencyResponse)
def classify_urgency(note: ClinicalNote):
    """
    Classify the urgency level of a clinical note.
    
    Uses ZERO-SHOT classification — no medical training data needed!
    The model reasons about urgency from general language understanding.
    Great for rapid prototyping before you have labeled data.
    """
    urgency_labels = [
        "life-threatening emergency",
        "urgent - needs attention within hours",
        "routine - can wait for next appointment",
        "administrative - no clinical urgency",
    ]

    if MODEL_LOADED:
        try:
            result = classifier(note.text, candidate_labels=urgency_labels)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")
    else:
        # Demo mode
        result = {
            "labels": urgency_labels,
            "scores": [0.65, 0.25, 0.08, 0.02],
            "sequence": note.text,
        }

    scores_dict = dict(zip(result["labels"], [round(s, 3) for s in result["scores"]]))

    return UrgencyResponse(
        text=note.text,
        urgency_level=result["labels"][0],
        confidence=round(result["scores"][0], 3),
        all_scores=scores_dict,
    )


@app.post("/analyze-full")
def analyze_full(note: ClinicalNote):
    """
    Combined endpoint: runs both NER and urgency classification in one call.
    This is the 'production' endpoint a clinician dashboard would call.
    """
    entities_result = extract_entities(note)
    urgency_result = classify_urgency(note)

    return {
        "patient_id": note.patient_id,
        "entities": entities_result.entity_summary,
        "urgency": {
            "level": urgency_result.urgency_level,
            "confidence": urgency_result.confidence,
        },
        "raw_text_length": len(note.text),
        "total_entities_found": len(entities_result.entities),
    }


# ── EXPERIMENT ZONE ────────────────────────────────────────────────────────────
# Try adding a new endpoint! Ideas:
#
# @app.post("/summarize")
# def summarize_note(note: ClinicalNote):
#     summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
#     result = summarizer(note.text, max_length=60, min_length=20)
#     return {"summary": result[0]["summary_text"]}
#
# @app.post("/translate-to-patient")
# def patient_friendly(note: ClinicalNote):
#     """Convert clinical jargon to plain language using a text2text model"""
#     pass
