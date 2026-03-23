# Lab 01 — Your First REST API

> **Goal:** Build a working FastAPI server step by step, learning one
> HTTP verb at a time.

> **Time:** ~30 minutes

> **Prerequisites:** [Lab 00 — REST Fundamentals](../lab_00_rest_fundamentals/README.md)

---

## What You'll Learn

- How to create a FastAPI application
- How to implement GET, POST, PUT, PATCH, and DELETE — one at a time
- How to use path parameters and query parameters
- How to return the correct HTTP status codes
- How Pydantic validates input automatically

---

## Setup

```bash
# Make sure you've installed dependencies
uv sync --extra dev

# Run the server (from the project root)
cd lab_01_your_first_api
uvicorn app:app --reload
```

The `--reload` flag restarts the server whenever you save a change —
this is key for the step-by-step approach below.

---

## How This Lab Works

Open [app.py](app.py). You'll see that **only GET is active**. The
other verbs (POST, PUT, PATCH, DELETE) are commented out. You will
uncomment them one at a time, save the file, and try each one in the
browser.

---

## Step 1 — GET (already active)

Open these URLs in your browser:

| URL | What It Shows |
|---|---|
| http://127.0.0.1:8000/ | Welcome page — confirms the API is running |
| http://127.0.0.1:8000/docs | Interactive Swagger UI — try every endpoint! |
| http://127.0.0.1:8000/v1/patients | JSON list of all patients |

**Try in the Swagger UI (`/docs`):**
- Click `GET /v1/patients` → "Try it out" → "Execute"
- Try filtering: set `gender` to `female` and execute again
- Click `GET /v1/patients/{patient_id}` → paste an ID from the list → execute
- Try a fake ID like `nonexistent` — you should get **404 Not Found**

---

## Step 2 — POST (create a patient)

1. Open `app.py`
2. Find **STEP 2** and uncomment the `create_patient` function
3. Save the file (the server restarts automatically)
4. Go to `/docs` and find the new `POST /v1/patients` endpoint
5. Click "Try it out", fill in a name/age/gender, and execute

**Notice:** The response code is **201 Created**, not 200. This is the
correct REST status code for creating a new resource.

---

## Step 3 — PUT (replace a patient)

1. Uncomment **STEP 3** in `app.py` and save
2. In `/docs`, try `PUT /v1/patients/{patient_id}`
3. You must send **all** fields (name, age, gender) — PUT replaces
   the entire record

**Try this:** Send a PUT with only `{"name": "New Name"}` — what
happens? (Hint: FastAPI returns 422 because age and gender are missing.)

---

## Step 4 — PATCH (update part of a patient)

1. Uncomment **STEP 4** in `app.py` and save
2. In `/docs`, try `PATCH /v1/patients/{patient_id}`
3. Send only `{"age": 75}` — the name and gender stay the same!

**PUT vs PATCH:** PUT requires all fields. PATCH only needs the fields
you want to change. PATCH is more convenient for small updates.

---

## Step 5 — DELETE (remove a patient)

1. Uncomment **STEP 5** in `app.py` and save
2. In `/docs`, try `DELETE /v1/patients/{patient_id}`
3. The response is **204 No Content** — the patient is gone

**Try this:** After deleting, try to GET the same patient. You should
get **404 Not Found**.

---

## Summary of Status Codes You've Seen

| Verb | Success Code | Why |
|---|---|---|
| GET | 200 OK | Data retrieved successfully |
| POST | 201 Created | A new resource was created |
| PUT | 200 OK | Resource replaced successfully |
| PATCH | 200 OK | Resource updated successfully |
| DELETE | 204 No Content | Resource is gone, nothing to return |
| Any | 404 Not Found | The resource doesn't exist |
| Any | 422 Unprocessable Entity | Invalid input data |

---

## Step 6 — Challenges

Once you've uncommented all steps, try the challenges at the bottom
of [app.py](app.py):

1. **(Easy)** Add a `GET /v1/patients/count` endpoint
2. **(Medium)** Add a `min_age` query parameter to the list endpoint
3. **(Stretch)** Add a `POST /v1/patients/search` endpoint — see
   [solutions/lab_01_challenge3.md](../solutions/lab_01_challenge3.md)

---

## ✅ Done When

- [ ] You ran the server and saw the welcome page at `/`
- [ ] You uncommented and tried all 5 HTTP verbs one by one
- [ ] You got a 201 from POST, 204 from DELETE, 404 from a missing ID
- [ ] You understand the difference between PUT and PATCH
- [ ] You attempted at least one challenge

---

**Next →** [Lab 02: Train the Model](../lab_02_train_model/README.md)
