"""
Lab 01 — Your First REST API
=============================
A FastAPI server that manages patients. Start with just GET, then
uncomment one section at a time to learn each HTTP verb.

How to run:
    cd lab_01_your_first_api
    uvicorn app:app --reload

Then open http://127.0.0.1:8000/docs to explore the interactive docs.

How to work through this file:
    1. Run the server as-is — only GET works. Try it in /docs.
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
        "docs": "/docs",
        "patients": "/v1/patients",
    }


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
