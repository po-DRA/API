# Lab 06 — Challenge Solutions

## Challenge 1 (Easy): Cache stats endpoint

```python
@app.get("/v1/cache/stats", status_code=200, tags=["System"])
def cache_stats():
    """Show what's in the LLM response cache."""
    return {
        "data": {
            "cached_entries": len(llm_cache),
            "cache_keys": [
                {
                    "note_preview": key.split("|")[0][:50] + "...",
                    "model": key.split("|")[1],
                    "temperature": key.split("|")[2],
                }
                for key in llm_cache
            ],
        }
    }
```

Usage: `GET /v1/cache/stats`

---

## Challenge 2 (Medium): Summarize endpoint

A different prompt for a different task — same LLM, different behavior.
This shows the power of prompt engineering.

```python
class SummarizeRequest(BaseModel):
    note: str = Field(..., min_length=10, description="The clinical note to summarize")
    max_tokens: int = Field(100, ge=10, le=300, description="Max summary length")
    model: str = Field(DEFAULT_MODEL, description="HuggingFace model ID")


@app.post("/v1/summarize", status_code=201, tags=["LLM"])
def summarize_note(request: SummarizeRequest):
    """Summarize a long clinical note into key points."""
    _check_rate_limit()

    prompt = (
        "[INST] You are a clinical assistant. "
        "Summarize the following clinical note in 2-3 bullet points. "
        "Focus on: diagnosis, key findings, and recommended actions.\n\n"
        f"Clinical note: {request.note} [/INST]"
    )

    summary = _call_huggingface(
        prompt=prompt,
        model=request.model,
        temperature=0.3,  # Low temperature for factual summaries
        max_tokens=request.max_tokens,
    )

    return {
        "data": {
            "id": str(uuid4()),
            "note": request.note,
            "summary": summary,
            "model_used": request.model,
            "created_at": datetime.now(UTC).isoformat(),
        }
    }
```

Usage:
```json
POST /v1/summarize
{
  "note": "Patient is a 67-year-old male presenting to the ED with acute onset chest pain radiating to the left arm, associated with diaphoresis and nausea. ECG shows ST-elevation in leads II, III, and aVF. Troponin I elevated at 2.4 ng/mL. Started on heparin drip and aspirin. Cardiology consulted for emergent catheterization."
}
```

> **Note:** Temperature is set to 0.3 (low) because summaries should be
> factual and consistent, not creative.

---

## Challenge 3 (Stretch): Combined ML + LLM endpoint

This is the "best of both worlds" pattern. Your ML model does fast
classification, and the LLM explains the reasoning.

```python
import joblib

# Load the ML model from Lab 03
ML_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "urgency_classifier.joblib",
)
ml_model = None
if os.path.exists(ML_MODEL_PATH):
    ml_model = joblib.load(ML_MODEL_PATH)


class AnalyzeRequest(BaseModel):
    note: str = Field(..., min_length=10, description="The clinical note to analyze")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(150, ge=10, le=500)


@app.post("/v1/analyze", status_code=201, tags=["LLM"])
def analyze_note(request: AnalyzeRequest):
    """
    Full analysis: ML classification + LLM explanation.

    1. Your ML model predicts urgent/routine (instant)
    2. The LLM explains why (2-10 seconds)
    3. You get both in one response
    """
    _check_rate_limit()

    # Step 1: ML prediction (fast)
    ml_result = None
    if ml_model is not None:
        prediction = ml_model.predict([request.note])[0]
        probabilities = ml_model.predict_proba([request.note])[0]
        confidence = float(max(probabilities))
        ml_result = {
            "prediction": prediction,
            "confidence": round(confidence, 4),
        }

    # Step 2: LLM explanation (slower)
    prompt = (
        "[INST] You are a clinical assistant. "
        "Given the following clinical note, explain in 2-3 sentences "
        "whether this is urgent or routine and why.\n\n"
        f"Clinical note: {request.note} [/INST]"
    )
    explanation = _call_huggingface(
        prompt=prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    return {
        "data": {
            "id": str(uuid4()),
            "note": request.note,
            "ml_classification": ml_result,
            "llm_explanation": explanation,
            "created_at": datetime.now(UTC).isoformat(),
        },
        "meta": {
            "ml_model": "TF-IDF + LogReg" if ml_model else "not loaded",
            "llm_model": DEFAULT_MODEL,
        },
    }
```

Usage:
```json
POST /v1/analyze
{
  "note": "Patient presents with acute chest pain, ST-elevation on ECG, and elevated troponin levels requiring immediate intervention"
}
```

Response:
```json
{
  "data": {
    "id": "abc-123...",
    "note": "Patient presents with acute chest pain...",
    "ml_classification": {
      "prediction": "urgent",
      "confidence": 0.9512
    },
    "llm_explanation": "This note suggests an urgent case. ST-elevation on ECG indicates...",
    "created_at": "2026-..."
  },
  "meta": {
    "ml_model": "TF-IDF + LogReg",
    "llm_model": "mistralai/Mistral-7B-Instruct-v0.3"
  }
}
```

> **Production insight:** The ML model responds in ~1ms, the LLM in
> ~2-10 seconds. In a real system, you might return the ML prediction
> immediately and stream the LLM explanation as it generates.
