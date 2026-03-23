# 🚀 Step 1 — Hello API: Your First FastAPI Server

> ⏱ **Time: ~10 minutes** | First working API in under 5 minutes

---

## What You'll Learn

- How to start a FastAPI server
- The difference between GET and POST
- How FastAPI auto-generates documentation (this is magic ✨)
- The exact pattern every ML API will follow

---

## ▶️ Start It (in GitHub Codespaces or locally)

```bash
cd step_01_hello_api
uvicorn app:app --reload --port 8000
```

You'll see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

## 🔍 Explore These URLs

| URL | What it does |
|-----|-------------|
| `http://localhost:8000/` | Root — the "heartbeat" |
| `http://localhost:8000/docs` | **Auto-generated Swagger UI** — try every endpoint here! |
| `http://localhost:8000/patient/P001` | URL parameter example |
| `http://localhost:8000/search?keyword=diabetes` | Query parameter example |

---

## 🧪 Test Your First POST Request

In the Swagger UI (`/docs`), click on **POST /analyze**, then **"Try it out"** and paste:

```json
{
  "note_text": "Patient presents with severe chest pain and shortness of breath",
  "patient_id": "P001"
}
```

You'll get back a JSON response. This is **exactly** the pattern your ML model will use.

---

## 💡 Key Insight: OpenAPI is Built In

FastAPI automatically generates an **OpenAPI spec** for you. The `/docs` page IS the documentation — you don't write it separately. Every parameter, type, and example is extracted from your Python code.

This means: **your code is your documentation.** No extra work.

---

## 🔬 What's Happening Inside `app.py`

```
FastAPI app
    │
    ├── GET  /                    ← No input, returns status
    ├── GET  /patient/{id}        ← Input in URL path
    ├── GET  /search?keyword=...  ← Input as query parameter
    └── POST /analyze             ← Input as JSON body ← THIS IS YOUR ML PATTERN
```

The `POST /analyze` endpoint is the template for every ML prediction endpoint you'll ever build.

---

## ✏️ Challenge (Optional)

Open `app.py` and add a new endpoint at the bottom. Ideas:
- `GET /medications/{drug_name}` — return fake drug info
- `POST /icd-lookup` — accept a symptom description, return a fake ICD-10 code

After saving, the server reloads automatically (that's what `--reload` does). Check `/docs` — your new endpoint appears immediately.

---

➡️ **Next: [Step 2 — Real Medical NLP Model →](../step_02_medical_api/README.md)**
