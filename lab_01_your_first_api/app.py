"""
Lab 01 — Your First REST API
=============================
A FastAPI server that teaches REST step by step.

How to run:
    cd lab_01_your_first_api
    uvicorn app:app --reload

How to work through this file:
    0. Run the server. Open http://127.0.0.1:8000/play to try
       the add-two-numbers mini-app — your first API call!
    1. Explore the patient GET endpoints at /docs.
    2. Uncomment STEP 2 (POST), save, and try creating a patient.
    3. Uncomment STEP 3 (PUT), save, and try replacing a patient.
    4. Uncomment STEP 4 (PATCH), save, and try a partial update.
    5. Uncomment STEP 5 (DELETE), save, and try removing a patient.

    The --reload flag means the server restarts every time you save!

Reference:
    - FastAPI docs: https://fastapi.tiangolo.com/
    - Build a FastAPI in minutes: https://realpython.com/fastapi-python-web-apis/
    - REST cheatsheet: https://bytebytego.com/guides/rest-api-cheatsheet/
"""

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

# ── Create the FastAPI application ──────────────────────────────────
app = FastAPI(
    title="Patient Management API",
    description="Lab 01 — Learn REST verbs with a healthcare example",
    version="1.0.0",
)


# ── Root endpoint ───────────────────────────────────────────────────
@app.get("/", status_code=200, tags=["System"])
def root():
    """Welcome page — confirms the API is running."""
    return {
        "message": "Patient Management API is running!",
        "try_first": "/play",
        "docs": "/docs",
        "patients": "/v1/patients",
    }


# =====================================================================
#  STEP 0 — Your very first API endpoint + a mini UI to try it
# =====================================================================
# This is the simplest possible API: send two numbers, get the sum.
# Open http://127.0.0.1:8000/play to try it with a visual interface.
#
# What this teaches:
#   - An API endpoint is just a Python function with a URL
#   - Query parameters (?a=5&b=3) pass data to the function
#   - The function returns JSON automatically
#   - A UI (or any client) can call this endpoint via HTTP
# =====================================================================


@app.get("/add", status_code=200, tags=["Step 0 — Try It"])
def add(a: int, b: int):
    """
    Add two numbers. Try it:  /add?a=5&b=3

    This is the simplest API endpoint you can build.
    - `a` and `b` are query parameters (they go after the ? in the URL)
    - FastAPI converts them to integers automatically
    - The result is returned as JSON
    """
    return {"a": a, "b": b, "result": a + b}


@app.get("/play", response_class=HTMLResponse, tags=["Step 0 — Try It"])
def play():
    """
    A tiny web page to try the /add endpoint visually.

    This shows how a frontend (HTML + JavaScript) calls a backend (API).
    The browser is the CLIENT. Your FastAPI server is the SERVER.
    When you click "Calculate", JavaScript calls GET /add?a=...&b=...
    and displays the JSON response.
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>My First API</title>
        <style>
            body {
                font-family: system-ui, sans-serif;
                max-width: 500px;
                margin: 80px auto;
                padding: 0 20px;
                background: #f8f9fa;
            }
            h1 { color: #2c3e50; }
            .card {
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            input {
                width: 80px;
                padding: 10px;
                font-size: 24px;
                text-align: center;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
            button {
                padding: 10px 24px;
                font-size: 18px;
                background: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }
            button:hover { background: #2980b9; }
            .result {
                margin-top: 20px;
                padding: 15px;
                background: #eafaf1;
                border-radius: 8px;
                font-size: 18px;
                display: none;
            }
            .api-call {
                margin-top: 12px;
                padding: 10px;
                background: #f5f5f5;
                border-radius: 6px;
                font-family: monospace;
                font-size: 13px;
                color: #666;
                display: none;
            }
            .row { display: flex; align-items: center; gap: 12px; margin: 16px 0; }
            .plus { font-size: 28px; color: #888; }
        </style>
    </head>
    <body>
        <h1>My First API</h1>
        <div class="card">
            <p>Enter two numbers. When you click <b>Calculate</b>, the browser
               calls your API at <code>/add?a=...&b=...</code> and shows the
               JSON response.</p>
            <div class="row">
                <input type="number" id="a" value="5">
                <span class="plus">+</span>
                <input type="number" id="b" value="3">
                <button onclick="callAPI()">Calculate</button>
            </div>
            <div class="result" id="result"></div>
            <div class="api-call" id="api-call"></div>
        </div>
        <p style="margin-top:20px; color:#888; font-size:14px;">
            Now open <a href="/docs">/docs</a> to see the same endpoint
            in FastAPI's interactive Swagger UI.
        </p>
        <script>
            async function callAPI() {
                const a = document.getElementById('a').value;
                const b = document.getElementById('b').value;
                const url = `/add?a=${a}&b=${b}`;

                // Show which URL we're calling (so learners see the API call)
                const apiDiv = document.getElementById('api-call');
                apiDiv.style.display = 'block';
                apiDiv.textContent = 'GET ' + url;

                const response = await fetch(url);
                const data = await response.json();

                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = `<b>${data.a} + ${data.b} = ${data.result}</b>`
                    + `<br><span style="color:#888; font-size:14px;">`
                    + `API returned: ${JSON.stringify(data)}</span>`;
            }
        </script>
    </body>
    </html>
    """


# ── Patient model ──────────────────────────────────────────────────
# Pydantic validates incoming JSON automatically.
# If someone sends {"age": "banana"}, FastAPI returns 422 for us.


class Patient(BaseModel):
    """Fields for a patient record."""

    name: str = Field(..., examples=["Jane Doe"])
    age: int = Field(..., ge=0, le=150, examples=[45])
    gender: str = Field(..., examples=["female"])


# ── In-memory "database" ───────────────────────────────────────────
# In a real app this would be PostgreSQL, MongoDB, etc.
# We use a simple dict keyed by patient ID.
patients_db: dict[str, dict] = {}


# ── Seed data so the API isn't empty on startup ────────────────────
_seed = [
    {"name": "Alice Smith", "age": 34, "gender": "female"},
    {"name": "Bob Johnson", "age": 72, "gender": "male"},
    {"name": "Carol Williams", "age": 58, "gender": "female"},
]
for _p in _seed:
    _id = str(uuid4())
    patients_db[_id] = {"id": _id, **_p}


# =====================================================================
#  STEP 1 — GET (already active!)
# =====================================================================
# GET is for READING data. It never changes anything on the server.
# This is the first endpoint learners see. Just run the server and
# open http://127.0.0.1:8000/v1/patients in your browser.
# =====================================================================


@app.get("/v1/patients", status_code=200, tags=["Patients"])
def list_patients(
    gender: str | None = Query(None, description="Filter by gender"),
    limit: int = Query(10, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    List all patients.

    REST notes:
    - GET = read data. The server returns 200 OK.
    - Query params (?gender=female) filter the results.
    - limit/offset handle pagination.
    """
    results = list(patients_db.values())

    if gender:
        results = [p for p in results if p["gender"].lower() == gender.lower()]

    total = len(results)
    results = results[offset : offset + limit]

    return {
        "data": results,
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@app.get("/v1/patients/{patient_id}", status_code=200, tags=["Patients"])
def get_patient(patient_id: str):
    """
    Get one patient by ID.

    REST notes:
    - {patient_id} in the URL is a PATH PARAMETER — it answers "which one?"
    - Returns 404 if the patient doesn't exist.
    """
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"data": patients_db[patient_id]}


# =====================================================================
#  STEP 2 — POST (Uncomment the block below, then save)
# =====================================================================
# POST means "create a new resource". The server assigns the ID.
# After uncommenting, go to /docs, find POST /v1/patients, click
# "Try it out", and create a patient. Notice the 201 status code!
# =====================================================================

# @app.post("/v1/patients", status_code=201, tags=["Patients"])
# def create_patient(patient: Patient):
#     """
#     Create a new patient.
#
#     REST notes:
#     - POST creates something NEW. The server generates the ID.
#     - Returns 201 Created (not 200!) because a new resource was made.
#     - If the client sends bad data (e.g. age = -5), FastAPI returns 422.
#     """
#     patient_id = str(uuid4())
#     record = {"id": patient_id, **patient.model_dump()}
#     patients_db[patient_id] = record
#     return {"data": record}


# =====================================================================
#  STEP 3 — PUT (Uncomment the block below, then save)
# =====================================================================
# PUT means "replace the entire resource". The client must send ALL
# fields, even the ones that didn't change.
# Try it: PUT a patient with a different name AND age AND gender.
# =====================================================================

# @app.put("/v1/patients/{patient_id}", status_code=200, tags=["Patients"])
# def replace_patient(patient_id: str, patient: Patient):
#     """
#     Replace a patient record entirely.
#
#     REST notes:
#     - PUT replaces the WHOLE resource. Every field must be sent.
#     - Returns 404 if the patient doesn't exist.
#     """
#     if patient_id not in patients_db:
#         raise HTTPException(status_code=404, detail="Patient not found")
#     record = {"id": patient_id, **patient.model_dump()}
#     patients_db[patient_id] = record
#     return {"data": record}


# =====================================================================
#  STEP 4 — PATCH (Uncomment the block below, then save)
# =====================================================================
# PATCH means "update only the fields I'm sending". Unlike PUT, you
# don't have to resend everything.
# Try it: PATCH a patient and send ONLY {"age": 75}. The name and
# gender should stay the same.
# =====================================================================

# class PatientPatch(BaseModel):
#     """For partial updates — every field is optional."""
#     name: str | None = None
#     age: int | None = Field(None, ge=0, le=150)
#     gender: str | None = None
#
#
# @app.patch("/v1/patients/{patient_id}", status_code=200, tags=["Patients"])
# def update_patient(patient_id: str, updates: PatientPatch):
#     """
#     Partially update a patient.
#
#     REST notes:
#     - PATCH updates only the provided fields.
#     - PUT would require ALL fields — PATCH is more convenient.
#     """
#     if patient_id not in patients_db:
#         raise HTTPException(status_code=404, detail="Patient not found")
#     existing = patients_db[patient_id]
#     patch_data = updates.model_dump(exclude_unset=True)
#     existing.update(patch_data)
#     return {"data": existing}


# =====================================================================
#  STEP 5 — DELETE (Uncomment the block below, then save)
# =====================================================================
# DELETE removes a resource. We return 204 No Content because the
# thing is gone — there's nothing to send back.
# Try it: DELETE a patient, then try to GET them. You should get 404.
# =====================================================================

# @app.delete("/v1/patients/{patient_id}", status_code=204, tags=["Patients"])
# def delete_patient(patient_id: str):
#     """
#     Delete a patient.
#
#     REST notes:
#     - Returns 204 No Content on success (the resource is gone).
#     - Returns 404 if the patient didn't exist.
#     """
#     if patient_id not in patients_db:
#         raise HTTPException(status_code=404, detail="Patient not found")
#     del patients_db[patient_id]


# =====================================================================
#  STEP 6 — YOUR TURN (try these after uncommenting all steps above)
# =====================================================================
#
# Challenge 1 (Easy):
#   Add a GET /v1/patients/count endpoint that returns:
#   {"count": <number>}
#   What status code should it return?
#
# Challenge 2 (Medium):
#   Add a min_age query parameter to list_patients so clients can do:
#   GET /v1/patients?min_age=65
#
# Challenge 3 (Stretch):
#   Add a POST /v1/patients/search endpoint that accepts a JSON body
#   with a "query" field and returns patients whose name matches
#   (case-insensitive). Why POST for a search instead of GET?
#   See solutions/lab_01_challenge3.md for the answer.
