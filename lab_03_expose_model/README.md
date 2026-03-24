# Lab 03: Expose the Model as a REST API

> **Goal:** Serve the trained urgency classifier as a REST API so
> anyone can send a clinical note and get a prediction back.

> **Time:** ~30 minutes

> **Prerequisites:**
> [Lab 02: Train the Model](../lab_02_train_model/README.md) (model
> must be trained first)

---

## What You'll Learn

- How to load an ML model at API startup (lifespan context)
- How to design prediction endpoints following REST principles
- How to return confidence scores alongside predictions
- How to store and retrieve prediction history

---

## Setup

```bash
# 1. Go back to the project root (if you're not already there)
cd ..

# 2. Make sure the model is trained
python lab_02_train_model/train.py

# 3. Start the prediction API
cd lab_03_expose_model
uvicorn app:app --reload
```

Open http://127.0.0.1:8000/docs to explore.

---

## Endpoints Overview

| Method | Endpoint | What It Does | Status Code |
|---|---|---|---|
| POST | `/v1/predictions` | Classify a clinical note | 201 |
| GET | `/v1/predictions` | List stored predictions | 200 |
| GET | `/v1/predictions/{id}` | Get one prediction | 200 / 404 |
| DELETE | `/v1/predictions/{id}` | Delete a prediction | 204 / 404 |
| GET | `/v1/model/info` | Model metadata | 200 / 503 |

---

## Try It

### Submit a prediction
```bash
curl -X POST http://127.0.0.1:8000/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"note": "Patient has acute chest pain radiating to left arm with diaphoresis"}'
```

Expected response (201 Created):
```json
{
  "data": {
    "id": "abc-123...",
    "note": "Patient has acute chest pain...",
    "prediction": "urgent",
    "confidence": 0.9812,
    "created_at": "2025-..."
  },
  "meta": {"model_version": "2025-..."}
}
```

### List all predictions
```bash
curl http://127.0.0.1:8000/v1/predictions
```

### Filter by label
```bash
curl "http://127.0.0.1:8000/v1/predictions?prediction=urgent"
```

### Check model info
```bash
curl http://127.0.0.1:8000/v1/model/info
```

---

## Key Architecture Decisions

Read through [app.py](app.py). Every decision is commented.  The
highlights:

1. **Model loaded once at startup**, not on every request.  Loading a
   model from disk can take hundreds of milliseconds.  Doing it once
   saves all that time for every subsequent request.

2. **Predictions stored with UUIDs:** clients can retrieve, list, and
   delete them later.  This is REST: predictions are a *resource*.

3. **Consistent response envelope:** every response is
   `{data: ..., meta: ...}`.  Clients always know where to find the
   payload.

4. **503 when model missing:** the API starts even without a model,
   but prediction endpoints return `503 Service Unavailable` with a
   helpful message.

---

## Why Is My Confidence Score Low?

If you see confidence around ~0.54 for every prediction, that's expected!
Our training dataset has only 35 samples, so the model has a limited
vocabulary.  Short or vague notes like *"Patient had fever"* don't
contain the specific medical phrases the model learned from (e.g.
"ST-elevation", "troponin", "hemodynamically unstable").

Try a note that uses words from the training data and you'll see higher
confidence:

```bash
curl -X POST http://127.0.0.1:8000/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"note": "Patient presents with acute chest pain, ST-elevation on ECG, and elevated troponin levels requiring immediate intervention"}'
```

This is a real-world ML lesson: **models are only as good as their
training data.**  More data and richer vocabulary = better predictions.

---

## 🎯 Challenges

See the YOUR TURN section at the bottom of [app.py](app.py):

1. **(Easy)** Add a stats endpoint
2. **(Medium)** Add confidence filtering
3. **(Stretch)** Add batch predictions

---

## ✅ Done When

- [ ] You can POST a clinical note and get a prediction back (201)
- [ ] You can GET the list of predictions with filtering
- [ ] You can DELETE a prediction (204)
- [ ] The `/v1/model/info` endpoint returns model metadata
- [ ] You understand why the model is loaded at startup, not per-request

---

**Next →** [Lab 04: Test the API](../lab_04_test_api/README.md)
