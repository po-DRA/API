"""
Step 3 — Background Tasks & Job Queue
======================================
What if your model takes 30 seconds? Or 10 minutes? (Think: whole-slide imaging)

You can't make the caller wait. Instead:
  1. Accept the job, return a job_id immediately
  2. Run the model in the background
  3. Caller polls: "is job 42 done yet?"
  4. When done, return results

This is the standard pattern for:
  - Large image analysis (pathology slides)
  - Batch processing of hundreds of notes
  - Any model that takes > 3-5 seconds

Run it:
  cd step_03_live_model
  uvicorn app:app --reload --port 8000
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
import asyncio
import uuid
import time

app = FastAPI(
    title="Async Medical Analysis API",
    description="""
    Demonstrates the background job pattern for long-running ML models.
    
    Pattern:
    1. POST /jobs/analyze → returns job_id immediately
    2. GET  /jobs/{job_id} → check status (pending/running/complete/failed)
    3. GET  /jobs/{job_id}/result → get the actual results
    """,
    version="3.0.0",
)


# ── In-memory job store ────────────────────────────────────────────────────────
# In production, replace this with Redis or a database!
jobs: dict = {}


class Job(BaseModel):
    job_id: str
    status: Literal["pending", "running", "complete", "failed"]
    created_at: str
    completed_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# ── Simulated ML models ────────────────────────────────────────────────────────
async def run_slow_model(job_id: str, text: str, model_type: str):
    """
    Simulates a slow model (like whole-slide image analysis).
    
    In reality, replace `await asyncio.sleep()` with your actual model call.
    The key: run it in the background so the API stays responsive.
    """
    jobs[job_id]["status"] = "running"

    try:
        # Simulate different processing times for different models
        processing_times = {
            "quick_ner": 2,         # Fast: NER on short text
            "full_analysis": 8,     # Medium: NER + classification + summary
            "slide_analysis": 15,   # Slow: Pathology slide (simulated)
        }
        wait_time = processing_times.get(model_type, 5)

        # Simulate model running...
        await asyncio.sleep(wait_time)

        # Fake results based on model type
        if model_type == "quick_ner":
            result = {
                "entities": ["diabetes", "metformin", "HbA1c"],
                "processing_time_s": wait_time,
            }
        elif model_type == "full_analysis":
            result = {
                "entities": ["stage III colorectal cancer", "FOLFOX", "KRAS"],
                "urgency": "urgent",
                "summary": "Oncology patient requiring chemotherapy initiation.",
                "recommended_specialists": ["oncology", "surgery"],
                "processing_time_s": wait_time,
            }
        elif model_type == "slide_analysis":
            result = {
                "tissue_type": "adenocarcinoma",
                "grade": "grade_2",
                "mitotic_index": 12,
                "tumor_percentage": 0.35,
                "confidence": 0.91,
                "regions_analyzed": 1247,
                "processing_time_s": wait_time,
            }
        else:
            result = {"status": "unknown model type"}

        jobs[job_id]["status"] = "complete"
        jobs[job_id]["result"] = result
        jobs[job_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


# ── Request models ─────────────────────────────────────────────────────────────
class AnalysisRequest(BaseModel):
    text: str
    model_type: Literal["quick_ner", "full_analysis", "slide_analysis"] = "quick_ner"
    patient_id: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Patient with stage III colorectal cancer, KRAS wild-type",
                    "model_type": "full_analysis",
                    "patient_id": "P001"
                }
            ]
        }
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "service": "Async Medical Analysis API",
        "pattern": "Submit job → poll status → retrieve results",
        "active_jobs": len(jobs),
    }


@app.post("/jobs/analyze", status_code=202)
def submit_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Submit an analysis job. Returns IMMEDIATELY with a job_id.
    Status 202 = "Accepted" (not done yet, but will be)
    
    The model runs in the background.
    Poll /jobs/{job_id} to check progress.
    """
    job_id = str(uuid.uuid4())[:8]  # Short readable ID

    # Create the job record
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "patient_id": request.patient_id,
        "model_type": request.model_type,
        "completed_at": None,
        "result": None,
        "error": None,
    }

    # This returns immediately — model runs in background
    background_tasks.add_task(run_slow_model, job_id, request.text, request.model_type)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Job submitted. Poll GET /jobs/{job_id} to check status.",
        "expected_wait_s": {"quick_ner": 2, "full_analysis": 8, "slide_analysis": 15}
            .get(request.model_type, 5),
    }


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    Check the status of a submitted job.
    Status will be: pending → running → complete (or failed)
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return jobs[job_id]


@app.get("/jobs/{job_id}/result")
def get_job_result(job_id: str):
    """
    Get results once job is complete.
    Returns 400 if job is still running.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs[job_id]

    if job["status"] == "pending":
        return {"message": "Job is queued, not started yet", "status": "pending"}
    elif job["status"] == "running":
        return {"message": "Model is currently running...", "status": "running"}
    elif job["status"] == "failed":
        raise HTTPException(status_code=500, detail=job.get("error", "Unknown error"))
    else:
        return {
            "job_id": job_id,
            "status": "complete",
            "result": job["result"],
            "completed_at": job["completed_at"],
        }


@app.get("/jobs")
def list_jobs():
    """List all jobs and their statuses"""
    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": jid,
                "status": j["status"],
                "model_type": j.get("model_type"),
                "created_at": j["created_at"],
            }
            for jid, j in jobs.items()
        ],
    }


@app.delete("/jobs/{job_id}")
def delete_job(job_id: str):
    """Clean up a completed job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    del jobs[job_id]
    return {"message": f"Job {job_id} deleted"}
