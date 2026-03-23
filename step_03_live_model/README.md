# ⚡ Step 3 — Background Tasks: When Models Take Too Long

> ⏱ **Time: ~10 minutes** | The pattern for heavy models

---

## The Problem

Your whole-slide pathology model takes **15 seconds**. Your batch processing job takes **2 minutes**. 

You **cannot** make the caller wait — HTTP requests time out, users get frustrated, mobile apps crash.

## The Solution: The Job Queue Pattern

```
Instead of:    Send request → wait 15s → get result
Do this:       Send request → get job_id immediately (< 1s)
               Poll every 2s → "still running..."  
               Eventually → "complete! here are your results"
```

---

## ▶️ Start the Server

```bash
cd step_03_live_model
uvicorn app:app --reload --port 8000
```

---

## 🧪 Walk Through the Full Flow

### Step 1: Submit a job (returns INSTANTLY)
```bash
curl -X POST http://localhost:8000/jobs/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Pathology slide: adenocarcinoma tissue", "model_type": "slide_analysis"}'
```

Response (instant!):
```json
{
  "job_id": "a3f2c1d9",
  "status": "pending",
  "message": "Job submitted. Poll GET /jobs/a3f2c1d9 to check status.",
  "expected_wait_s": 15
}
```

### Step 2: Poll for status
```bash
curl http://localhost:8000/jobs/a3f2c1d9
```

```json
{"status": "running", ...}
```

### Step 3: Get results when done
```bash
curl http://localhost:8000/jobs/a3f2c1d9/result
```

```json
{
  "result": {
    "tissue_type": "adenocarcinoma",
    "grade": "grade_2",
    "tumor_percentage": 0.35,
    "confidence": 0.91
  }
}
```

---

## 🏗️ Try All Three Model Types

In `/docs`, submit jobs with different `model_type` values:

| Model Type | Simulated Wait | Use Case |
|-----------|---------------|----------|
| `quick_ner` | 2 seconds | Fast NER on short notes |
| `full_analysis` | 8 seconds | NER + classification + summary |
| `slide_analysis` | 15 seconds | Pathology slide (heavy model) |

Submit multiple jobs at once — the server handles them all simultaneously!

---

## 💡 How It Works in the Code

```python
@app.post("/jobs/analyze", status_code=202)
def submit_analysis(request, background_tasks: BackgroundTasks):
    job_id = create_job_record()
    
    # Magic line — this returns immediately, model runs separately
    background_tasks.add_task(run_slow_model, job_id, request.text)
    
    return {"job_id": job_id, "status": "pending"}  # ← Returns NOW
```

`BackgroundTasks` is built into FastAPI — no extra dependencies needed.

**202 status code** means "Accepted" — the server says "I got your request and will process it."

---

## 🔄 Production Upgrade Path

The in-memory job store (`jobs: dict = {}`) works for learning but has limits:
- Restarts wipe all jobs
- Doesn't work across multiple server instances

For production, replace with:
```python
# Drop-in replacement: Redis job store
import redis
r = redis.Redis()
r.set(f"job:{job_id}", json.dumps(job_data))
```

Or use [Celery](https://docs.celeryq.dev/) for full job queue management.

---

➡️ **Next: [Step 4 — Deploy to Render →](../step_04_deploy_render/README.md)**

*(Put your API on the internet for free)*
