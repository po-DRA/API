# 🧬 Step 2 — Real Medical NLP Model

> ⏱ **Time: ~15 minutes** | First real ML predictions

---

## What You'll Build

A running API that extracts **diseases, drugs, genes** from clinical notes and classifies **urgency** — using real Hugging Face transformer models.

---

## ▶️ Start the Server

```bash
cd step_02_medical_api
uvicorn app:app --reload --port 8000
```

> ⚠️ **First run**: The model downloads ~500MB from Hugging Face. This takes 1–3 minutes. Every run after that is instant (it's cached).
> 
> If you're offline or in a hurry: the server falls back to **demo mode** and returns fake-but-correctly-structured results.

---

## 🔑 The Key Concept: Load Once, Serve Many

```python
# ✅ THIS — model loads once when server starts
ner_pipeline = pipeline("ner", model="d4data/biomedical-ner-all")

@app.post("/extract-entities")
def extract_entities(note):
    return ner_pipeline(note.text)  # Model already in memory!
```

```python
# ❌ NOT THIS — would reload the model on every request (30s wait!)
@app.post("/extract-entities")
def extract_entities(note):
    ner_pipeline = pipeline("ner", model="...")  # Reloads every time!
    return ner_pipeline(note.text)
```

This is the most important optimization for ML APIs.

---

## 🧪 Try These Examples

Open `http://localhost:8000/docs` and test **POST /extract-entities** with:

### Example 1 — Cardiology note
```json
{
  "text": "72-year-old male with acute myocardial infarction. On aspirin 100mg, atorvastatin 40mg. Family history of BRCA2 mutation.",
  "patient_id": "P001"
}
```

### Example 2 — Oncology note
```json
{
  "text": "Stage III colorectal cancer. Initiating FOLFOX chemotherapy. KRAS wild-type, MSI-H status confirmed.",
  "patient_id": "P002"
}
```

### Example 3 — Emergency note (urgency test)
```json
{
  "text": "Patient unresponsive, BP 60/40, suspected septic shock. Immediate ICU transfer required.",
  "patient_id": "P003"
}
```

---

## 💡 Zero-Shot Classification Explained

The `/classify-urgency` endpoint uses **zero-shot classification** — meaning the model was never trained on medical urgency labels. It reasons from general language understanding.

```python
urgency_labels = [
  "life-threatening emergency",
  "urgent - needs attention within hours",
  "routine - can wait for next appointment",
]
result = classifier(note.text, candidate_labels=urgency_labels)
```

**You can change these labels to anything** — no retraining needed! This is incredibly powerful for rapid prototyping before you have labeled training data.

---

## 📊 What the Response Looks Like

```json
{
  "patient_id": "P001",
  "entities": [
    {"entity_type": "Disease", "text": "myocardial infarction", "confidence": 0.98},
    {"entity_type": "Chemical", "text": "aspirin", "confidence": 0.96},
    {"entity_type": "Gene", "text": "BRCA2", "confidence": 0.93}
  ],
  "entity_summary": {
    "Disease": ["myocardial infarction"],
    "Chemical": ["aspirin", "atorvastatin"],
    "Gene": ["BRCA2"]
  },
  "processing_time_ms": 245.3,
  "model_used": "d4data/biomedical-ner-all"
}
```

---

## 🔬 Other Hugging Face Models to Try

Swap the model name in `app.py`:

| Task | Model | Use Case |
|------|-------|----------|
| NER | `allenai/scibert_scivocab_uncased` | Scientific text |
| NER | `sultan/BioM-ELECTRA-Large-SQuAD2` | Biomedical Q&A |
| Classification | Any `facebook/bart-large-mnli` | Zero-shot triage |
| Summarization | `Falconsai/medical_summarization` | Note summarization |
| Translation | `Helsinki-NLP/opus-mt-en-fr` | Multi-language notes |

---

## ✏️ Challenge

In `app.py`, find the **EXPERIMENT ZONE** at the bottom.

Uncomment the `/summarize` endpoint, and try summarizing a long clinical note. Check `/docs` — it appears immediately!

---

➡️ **Next: [Step 3 — Background Tasks →](../step_03_live_model/README.md)**

*(For when your model takes too long to run synchronously)*
