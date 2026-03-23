# Lab 03 — Challenge Solutions

## Challenge 1 (Easy): Root endpoint + Stats

Add a root `/` endpoint so visitors don't get a 404, and a
`/v1/predictions/stats` endpoint to show prediction counts.

```python
@app.get("/", status_code=200, tags=["System"])
def root():
    """Welcome page — confirms the API is running."""
    return {
        "message": "Clinical Urgency Prediction API is running!",
        "docs": "/docs",
        "predictions": "/v1/predictions",
        "model_info": "/v1/model/info",
    }


@app.get("/v1/predictions/stats", status_code=200, tags=["Predictions"])
def prediction_stats():
    """Count of predictions by label."""
    all_preds = list(predictions_db.values())
    return {
        "total": len(all_preds),
        "urgent": sum(1 for p in all_preds if p["prediction"] == "urgent"),
        "routine": sum(1 for p in all_preds if p["prediction"] == "routine"),
    }
```

> **Important:** Place the `/v1/predictions/stats` endpoint **before**
> `/v1/predictions/{prediction_id}` in your code. Otherwise FastAPI
> will treat `stats` as a prediction ID and return 404.

---

## Challenge 2 (Medium): Filter by confidence

Add a `min_confidence` query parameter to the list endpoint:

```python
@app.get("/v1/predictions", status_code=200, tags=["Predictions"])
def list_predictions(
    prediction: str | None = Query(None, description="Filter by label"),
    min_confidence: float | None = Query(None, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    results = list(predictions_db.values())

    if prediction:
        results = [r for r in results if r["prediction"] == prediction]

    if min_confidence is not None:
        results = [r for r in results if r["confidence"] >= min_confidence]

    total = len(results)
    results = results[offset : offset + limit]

    return {
        "data": results,
        "meta": {"total": total, "limit": limit, "offset": offset},
    }
```

Usage: `GET /v1/predictions?min_confidence=0.9`

---

## Challenge 3 (Stretch): Batch predictions

Accept a list of notes and return predictions for all of them in one
call. This reduces network round-trips.

```python
class BatchPredictionRequest(BaseModel):
    notes: list[str] = Field(..., min_length=1, description="List of clinical notes")


@app.post("/v1/predictions/batch", status_code=201, tags=["Predictions"])
def create_batch_predictions(request: BatchPredictionRequest):
    """Classify multiple clinical notes in one request."""
    _require_model()

    results = []
    for note in request.notes:
        prediction = model.predict([note])[0]
        probabilities = model.predict_proba([note])[0]
        confidence = float(max(probabilities))

        pred_id = str(uuid4())
        record = {
            "id": pred_id,
            "note": note,
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "created_at": datetime.now(UTC).isoformat(),
        }
        predictions_db[pred_id] = record
        results.append(record)

    return {
        "data": results,
        "meta": {"count": len(results)},
    }
```

Usage:
```json
POST /v1/predictions/batch
{
  "notes": [
    "Acute chest pain with ST-elevation and troponin rise",
    "Routine follow-up for managed hypothyroidism"
  ]
}
```
