# 🏥 Medical ML API Tutorial
### *From Zero to Deployed in 60 Minutes*

> **Built for:** Medical researchers with basic Python knowledge  
> **Goal:** Build a real NLP API that extracts entities from clinical notes and deploy it publicly  
> **Time:** ~1 hour | **Platform:** GitHub Codespaces (zero local setup needed)

---

## ⚡ Start in 30 Seconds (No Setup Required)

Click the button below to open this repo in a **cloud development environment** — Python, all dependencies, and VS Code, all ready instantly:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/YOUR_USERNAME/medical-ml-api-tutorial)

> **Don't have Codespaces?** GitHub gives you 60 free hours/month.  
> Or clone and run locally: `git clone ... && pip install -r requirements.txt`

---
<img width="2250" height="2752" alt="image" src="https://github.com/user-attachments/assets/d75bc383-d603-4cf2-b0a0-e5588d620a01" />
[link](https://bytebytego.com/guides/the-ultimate-api-learning-roadmap/)

## 🗺️ The 1-Hour Roadmap

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  ⏱ 0:00  Step 0 — Concepts (10 min)                              │
│           What is an API? When to use one? Key patterns.          │
│                                                                    │
│  ⏱ 0:10  Step 1 — Hello API (10 min)                             │
│           Your first running FastAPI server. GET + POST.          │
│                                                                    │
│  ⏱ 0:20  Step 2 — Real Medical NLP (15 min)                      │
│           HuggingFace NER model. Live inference. Zero-shot.       │
│                                                                    │
│  ⏱ 0:35  Step 3 — Background Tasks (10 min)                      │
│           For slow models: submit job → poll → get results.       │
│                                                                    │
│  ⏱ 0:45  Step 4 — Deploy to Render (10 min)                      │
│           Push to GitHub → live public URL → share with world.    │
│                                                                    │
│  ⏱ 0:55  Bonus — Choose Your Own Adventure                       │
│           Streamlit UI, batch processing, fine-tuning & more.     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## ❓ The Questions This Tutorial Answers

> *"What sort of projects are appropriate for APIs?"*

Anything you want to call automatically, repeatedly, or from other tools:
- Extract diagnoses from clinical notes → **API**
- Classify urgency of incoming referrals → **API**
- Identify drug interactions in a prescription → **API**
- Summarize a patient's history for a new specialist → **API**

> *"Can the model run in the background, or does it need pre-existing results?"*

**Both options are covered** — you'll build all three patterns:

| Pattern | When to use | Covered in |
|---------|------------|-----------|
| **Live inference** | Fast model (<3s), interactive use | Step 2 |
| **Pre-computed** | Results don't change, need speed | Step 2 (demo mode) |
| **Background jobs** | Slow model (>5s), batch processing | Step 3 |

---

## 📁 Repo Structure

```
medical-ml-api-tutorial/
│
├── 📖 README.md                    ← You are here
│
├── 🧠 step_00_concepts/
│   └── README.md                   ← API theory, no code
│
├── 🚀 step_01_hello_api/
│   ├── app.py                      ← First FastAPI server
│   └── README.md
│
├── 🧬 step_02_medical_api/
│   ├── app.py                      ← Real HuggingFace NER model
│   └── README.md
│
├── ⚡ step_03_live_model/
│   ├── app.py                      ← Background jobs pattern
│   └── README.md
│
├── 🌐 step_04_deploy_render/
│   ├── app.py                      ← Production-ready version
│   ├── render.yaml                 ← One-click Render config
│   └── README.md
│
├── .devcontainer/
│   └── devcontainer.json           ← GitHub Codespaces config
│
└── requirements.txt                ← All Python dependencies
```

---

## 🎯 Step-by-Step Guide

### [📖 Step 0 — Concepts](./step_00_concepts/README.md)
*What IS an API? When should I use one? What's the lifecycle?*

Start here if you want to understand the **why** before the **how**. Covers the key architectural decisions you'll face with ML models.

---

### [🚀 Step 1 — Hello API](./step_01_hello_api/README.md)

```bash
cd step_01_hello_api
uvicorn app:app --reload --port 8000
```

Open `http://localhost:8000/docs` — you'll see your first auto-documented API. Try clicking every endpoint.

**What you'll understand after this:** GET vs POST, URL parameters vs request body, Pydantic validation, the OpenAPI auto-docs.

---

### [🧬 Step 2 — Real Medical NLP](./step_02_medical_api/README.md)

```bash
cd step_02_medical_api
uvicorn app:app --reload --port 8000
```

Send this to `/extract-entities`:
```json
{
  "text": "Patient with acute myocardial infarction. On aspirin and metformin. BRCA1 positive.",
  "patient_id": "P001"
}
```

Get back:
```json
{
  "entities": [
    {"entity_type": "Disease", "text": "myocardial infarction", "confidence": 0.98},
    {"entity_type": "Chemical", "text": "aspirin", "confidence": 0.96},
    {"entity_type": "Gene", "text": "BRCA1", "confidence": 0.93}
  ]
}
```

**What you'll understand after this:** Model loading strategy, zero-shot classification, the real answer to "how does the model run?"

---

### [⚡ Step 3 — Background Tasks](./step_03_live_model/README.md)

```bash
cd step_03_live_model  
uvicorn app:app --reload --port 8000
```

Submit a "slow" job and watch it process asynchronously. This is the pattern for pathology image analysis, large batch jobs, or any model that takes >5 seconds.

**What you'll understand after this:** When NOT to use synchronous inference, how to build the submit→poll→retrieve pattern.

---

### [🌐 Step 4 — Deploy to Render](./step_04_deploy_render/README.md)

Your API goes public. Render is free, connects directly to GitHub, and needs zero DevOps knowledge.

**What you'll understand after this:** The full API lifecycle end-to-end, CORS for browser access, health checks, environment variables.

---

## 🌟 Bonus: Going Further

Once you've completed the 4 steps, here are natural next directions:

### 🖥️ Add a Streamlit Frontend
Let non-technical users interact with your API without knowing what an API is:

```bash
# In a new terminal:
streamlit run bonus/streamlit_frontend.py
```

### 📊 Try Different Medical Models

| Model | Task | HuggingFace Link |
|-------|------|-----------------|
| `d4data/biomedical-ner-all` | NER: diseases, drugs, genes | [🔗](https://huggingface.co/d4data/biomedical-ner-all) |
| `sultan/BioM-ELECTRA-Large-SQuAD2` | Medical Q&A | [🔗](https://huggingface.co/sultan/BioM-ELECTRA-Large-SQuAD2) |
| `Falconsai/medical_summarization` | Note summarization | [🔗](https://huggingface.co/Falconsai/medical_summarization) |
| `facebook/bart-large-mnli` | Zero-shot classification | [🔗](https://huggingface.co/facebook/bart-large-mnli) |
| `allenai/longformer-base-4096` | Long clinical documents | [🔗](https://huggingface.co/allenai/longformer-base-4096) |

### 🏋️ Fine-Tune on Your Own Data
Once you have labeled data, you can fine-tune any of these models:
```python
from transformers import Trainer, TrainingArguments
# Your data → better accuracy on your specific domain
```

### 🔐 Add Authentication
For real clinical data, add API key authentication:
```python
from fastapi.security import APIKeyHeader
```

### 📈 Add Monitoring
Track model performance over time with simple logging to a CSV or database.

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|---------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Port 8000 already in use | `uvicorn app:app --port 8001` |
| Model download is slow | Be patient (first time only, ~500MB). Or use demo mode by removing the transformers import. |
| Render deploy fails | Check build logs for missing packages; add to `requirements.txt` |
| CORS error from browser | Check CORS middleware in Step 4 — make sure your frontend URL is allowed |

---

## 📚 Reference Links

| Resource | What it's for |
|----------|-------------|
| [FastAPI Docs](https://fastapi.tiangolo.com/) | Everything FastAPI |
| [FastAPI in VS Code](https://code.visualstudio.com/docs/python/tutorial-fastapi) | IDE integration tips |
| [Hugging Face Tutorial](https://youtu.be/QEaBAZQCtwE) | Video intro to HF models |
| [Deploy NLP: FastAPI + Streamlit + HF Guide](https://towardsdatascience.com/deploy-nlp-models-with-fastapi-streamlit-and-hugging-face/) | Full stack deployment |
| [Build FastAPI in Minutes](https://realpython.com/fastapi-python-web-apis/) | Quick reference |
| [OpenAPI Specification](https://swagger.io/specification/) | Understanding auto-docs |
| [Render Docs](https://render.com/docs) | Deployment platform |

---

## 💬 Learning Community

Stuck? Have a question? Found a bug?

- Open an **Issue** on this repo
- Add your own experiment in a new branch and open a **Pull Request**
- The best way to learn is to break things and ask why

---

*Built for the medical research community. All models are for demonstration — not clinical use.*
