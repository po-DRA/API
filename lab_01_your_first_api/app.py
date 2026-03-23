"""
Lab 01 — Your First REST API
=============================
A working FastAPI server that manages a /v1/patients resource,
demonstrating all 5 HTTP verbs with correct REST status codes.

How to run:
    cd lab_01_your_first_api
    uvicorn app:app --reload

Then open http://127.0.0.1:8000/docs to explore the interactive docs.

Reference:
    - FastAPI docs: https://fastapi.tiangolo.com/
    - Build a FastAPI in minutes: https://realpython.com/fastapi-python-web-apis/
    - REST cheatsheet: https://bytebytego.com/guides/rest-api-cheatsheet/
"""

from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

# ── Create the FastAPI application ──────────────────────────────────
# metadata shows up in the auto-generated docs at /docs
app = FastAPI(
    title="Patient Management API",
    description="Lab 01 — Learn REST verbs with a healthcare example",
    version="1.0.0",
)


# ── Root endpoint ──────────────────────────────────────────────────
# Without this, visiting http://127.0.0.1:8000/ returns 404, which
# confuses beginners. A friendly landing page points them to /docs.


@app.get("/", status_code=200, tags=["System"])
def root():
    """Welcome page — directs users to the interactive docs."""
    return {
        "message": "Patient Management API is running!",
        "docs": "/docs",
        "patients": "/v1/patients",
    }


# ── Data model ──────────────────────────────────────────────────────
# Pydantic models validate incoming JSON automatically.
# If someone sends {"age": "banana"}, FastAPI returns 422 for us.


class PatientCreate(BaseModel):
    """Fields required when CREATING a new patient (POST)."""

    name: str = Field(..., examples=["Jane Doe"])
    age: int = Field(..., ge=0, le=150, examples=[45])
    condition: str = Field(..., examples=["hypertension"])


class PatientUpdate(BaseModel):
    """Fields for a FULL replacement (PUT) — all fields required."""

    name: str = Field(..., examples=["Jane Doe"])
    age: int = Field(..., ge=0, le=150, examples=[46])
    condition: str = Field(..., examples=["diabetes"])


class PatientPatch(BaseModel):
    """Fields for a PARTIAL update (PATCH) — every field is optional."""

    name: str | None = None
    age: int | None = Field(None, ge=0, le=150)
    condition: str | None = None


# ── In-memory "database" ───────────────────────────────────────────
# In a real app this would be PostgreSQL, MongoDB, etc.
# We use a dict so every verb (GET, POST, PUT, PATCH, DELETE) works.
patients_db: dict[str, dict] = {}


# ── Seed some sample data ──────────────────────────────────────────
# This makes the API more interesting to explore right away.
_seed = [
    {"name": "Alice Smith", "age": 34, "condition": "asthma"},
    {"name": "Bob Johnson", "age": 72, "condition": "atrial fibrillation"},
    {"name": "Carol Williams", "age": 58, "condition": "type 2 diabetes"},
]
for _p in _seed:
    _id = str(uuid4())
    patients_db[_id] = {"id": _id, **_p}


# =====================================================================
#  GET /v1/patients — List all patients (with filtering & pagination)
# =====================================================================
# GET is for READING data. It should NEVER modify anything on the server.
# We return 200 OK because the request succeeded.


@app.get("/v1/patients", status_code=200, tags=["Patients"])
def list_patients(
    # Query parameters let clients filter and paginate.
    # Example: GET /v1/patients?condition=asthma&limit=5&offset=0
    condition: str | None = Query(None, description="Filter by medical condition"),
    limit: int = Query(10, ge=1, le=100, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
):
    """
    List patients with optional filtering and pagination.

    REST notes:
    - Uses GET because we are READING, not creating or modifying.
    - Query params (?condition=X) filter the collection.
    - limit/offset implement pagination so clients don't get 1 million
      records at once.
    """
    results = list(patients_db.values())

    # Apply filter if the client sent ?condition=something
    if condition:
        results = [p for p in results if p["condition"].lower() == condition.lower()]

    # Total count BEFORE pagination (useful for the client to know how
    # many pages there are)
    total = len(results)

    # Slice for pagination
    results = results[offset : offset + limit]

    # Return a consistent response envelope: {data: [...], meta: {...}}
    return {
        "data": results,
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


# =====================================================================
#  GET /v1/patients/{patient_id} — Get one patient by ID
# =====================================================================
# The {patient_id} in the URL is a PATH PARAMETER.
# Path params identify a SPECIFIC resource (answer: "which one?").


@app.get("/v1/patients/{patient_id}", status_code=200, tags=["Patients"])
def get_patient(patient_id: str):
    """
    Retrieve a single patient by ID.

    REST notes:
    - Path parameter identifies the specific resource.
    - Returns 404 if the patient does not exist — this is the correct
      REST response for "resource not found".
    """
    if patient_id not in patients_db:
        # 404 = "I understood your request, but that thing doesn't exist."
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"data": patients_db[patient_id]}


# =====================================================================
#  POST /v1/patients — Create a new patient
# =====================================================================
# POST means "create a new resource". The server assigns the ID.
# We return 201 Created (NOT 200) because something new was created.


@app.post("/v1/patients", status_code=201, tags=["Patients"])
def create_patient(patient: PatientCreate):
    """
    Create a new patient record.

    REST notes:
    - POST creates a NEW resource. The server generates the ID.
    - Returns 201 Created with the new resource in the body.
    - If the client sends invalid data (e.g. age = -5), FastAPI
      automatically returns 422 Unprocessable Entity.
    """
    patient_id = str(uuid4())
    record = {"id": patient_id, **patient.model_dump()}
    patients_db[patient_id] = record
    return {"data": record}


# =====================================================================
#  PUT /v1/patients/{patient_id} — Replace a patient entirely
# =====================================================================
# PUT means "replace the entire resource with this new version".
# The client must send ALL fields, not just the ones that changed.


@app.put("/v1/patients/{patient_id}", status_code=200, tags=["Patients"])
def replace_patient(patient_id: str, patient: PatientUpdate):
    """
    Replace a patient record entirely.

    REST notes:
    - PUT replaces the WHOLE resource. Every field must be provided.
    - Returns 404 if the patient doesn't exist.
    - Returns 200 with the updated resource.
    """
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    record = {"id": patient_id, **patient.model_dump()}
    patients_db[patient_id] = record
    return {"data": record}


# =====================================================================
#  PATCH /v1/patients/{patient_id} — Update part of a patient
# =====================================================================
# PATCH means "update only the fields I'm sending".
# Unlike PUT, you don't have to resend the entire object.


@app.patch("/v1/patients/{patient_id}", status_code=200, tags=["Patients"])
def update_patient(patient_id: str, updates: PatientPatch):
    """
    Partially update a patient record.

    REST notes:
    - PATCH updates only the provided fields (partial update).
    - PUT would require ALL fields (full replacement).
    - Use PATCH when the client only knows one field changed.
    """
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    existing = patients_db[patient_id]

    # model_dump(exclude_unset=True) gives us ONLY the fields the
    # client actually sent, ignoring fields left as None.
    patch_data = updates.model_dump(exclude_unset=True)
    existing.update(patch_data)

    return {"data": existing}


# =====================================================================
#  DELETE /v1/patients/{patient_id} — Remove a patient
# =====================================================================
# DELETE removes a resource.
# We return 204 No Content because the thing is gone — there's nothing
# to send back.


@app.delete("/v1/patients/{patient_id}", status_code=204, tags=["Patients"])
def delete_patient(patient_id: str):
    """
    Delete a patient record.

    REST notes:
    - Returns 204 No Content on success (the resource is gone).
    - Returns 404 if the patient didn't exist to begin with.
    """
    if patient_id not in patients_db:
        raise HTTPException(status_code=404, detail="Patient not found")

    del patients_db[patient_id]
    # 204 means "success, nothing to return" — FastAPI handles this
    # automatically when status_code=204 and we return None.


# =====================================================================
#  🎯 YOUR TURN — Challenges
# =====================================================================
#
# Challenge 1 (Easy):
#   Add a GET /v1/patients/count endpoint that returns the total number
#   of patients as {"count": <number>}. What status code should it use?
#
# Challenge 2 (Medium):
#   Add a query parameter `min_age` to the list_patients endpoint so
#   clients can do GET /v1/patients?min_age=65 to find elderly patients.
#
# Challenge 3 (Stretch):
#   Add a POST /v1/patients/search endpoint that accepts a JSON body
#   with a "query" field and returns patients whose name or condition
#   matches (case-insensitive). Why might you use POST for a search
#   instead of GET?  (Hint: GET requests can't have a request body.)
#   See solutions/lab_01_challenge3.md for the answer.
