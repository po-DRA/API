# 🌐 Step 4 — Deploy to Render (Free!)

> ⏱ **Time: ~10 minutes** | Your API on the public internet

---

## What You'll Do

Take your local API and deploy it to a public URL so:
- Collaborators can call it from anywhere
- You can demo it from a browser
- A frontend app (React, Streamlit) can call it

**Cost: Free** on Render's free tier (512MB RAM, sleeps after 15 min inactivity).

---

## 📋 Prerequisites

- [ ] A [GitHub account](https://github.com) (free)
- [ ] A [Render account](https://render.com) — sign up with GitHub (free)
- [ ] This tutorial repo pushed to your GitHub

---

## 🚀 Deployment Steps

### 1. Push to GitHub

```bash
# In your Codespace terminal:
git add .
git commit -m "Add medical NLP API tutorial"
git push origin main
```

### 2. Connect to Render

1. Go to [render.com](https://render.com) → **New** → **Web Service**
2. Click **"Connect a repository"** → Select your GitHub repo
3. Fill in settings:

| Setting | Value |
|---------|-------|
| **Name** | `medical-nlp-api` (or any name) |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn step_04_deploy_render.app:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

4. Click **"Create Web Service"**

### 3. Wait ~3 minutes

Render builds your container, installs packages, and starts the server.
You'll see build logs in real-time.

### 4. Your API is live! 🎉

Visit `https://your-app-name.onrender.com/docs` — your Swagger UI is public!

---

## ⚠️ Free Tier Gotchas

| Issue | What it means | Solution |
|-------|--------------|----------|
| **Sleeps after 15 min** | First request takes ~30s to "wake up" | Expected behavior on free tier |
| **512MB RAM limit** | Large models (GPT-2, BERT-large) may crash | Use smaller models for free tier |
| **Model re-downloads on restart** | HuggingFace cache resets | Set `HF_HOME=/tmp/huggingface` in env vars |

---

## 🧪 Test Your Live API

```bash
# Replace with your actual Render URL
curl https://your-app.onrender.com/health

curl -X POST https://your-app.onrender.com/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient has hypertension and diabetes", "patient_id": "test-001"}'
```

---

## 📡 Calling Your API from Python (for collaborators)

Share this snippet with colleagues who want to use your model:

```python
import httpx

API_URL = "https://your-app.onrender.com"  # Replace with your URL

def extract_medical_entities(clinical_note: str) -> dict:
    """Call the medical NLP API — no Python ML libraries needed!"""
    response = httpx.post(
        f"{API_URL}/extract",
        json={"text": clinical_note, "patient_id": "research-001"}
    )
    response.raise_for_status()
    return response.json()

# Usage
note = "Patient with stage 2 breast cancer, BRCA1 positive, starting tamoxifen."
results = extract_medical_entities(note)
print(results["summary"])
# {'Disease': ['breast cancer'], 'Gene': ['BRCA1'], 'Chemical': ['tamoxifen']}
```

Your colleagues don't need FastAPI, transformers, or PyTorch installed — just `httpx`!

---

## 🌟 What You've Achieved

You've completed the full API lifecycle:
1. ✅ **Designed** — understood what the API should do
2. ✅ **Built** — FastAPI with Hugging Face models
3. ✅ **Tested** — Swagger UI, curl, Python client
4. ✅ **Documented** — auto-generated OpenAPI spec
5. ✅ **Deployed** — live on the public internet

---

## 📖 Resources

- [FastAPI Tutorial in VS Code](https://code.visualstudio.com/docs/python/tutorial-fastapi)
- [Deploying ML Models with FastAPI](https://www.analyticsvidhya.com/blog/2022/09/deploying-ml-models-using-fastapi/)
- [Hugging Face Model Hub](https://huggingface.co/models)
- [Render Documentation](https://render.com/docs)

---

➡️ **[Go back to the main README](../README.md)** to see the full picture and next steps
