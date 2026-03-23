# Lab 01 — Your First REST API

> **Goal:** Build a working FastAPI server that manages patients using
> all 5 HTTP verbs, with correct REST status codes.

> **Time:** ~30 minutes

> **Prerequisites:** [Lab 00 — REST Fundamentals](../lab_00_rest_fundamentals/README.md)

---

## What You'll Learn

- How to create a FastAPI application
- How to implement GET, POST, PUT, PATCH, and DELETE
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
perfect for development.

---

## Explore the API

Once the server is running, open these URLs in your browser:

| URL | What It Shows |
|---|---|
| http://127.0.0.1:8000/ | Welcome page — confirms the API is running |
| http://127.0.0.1:8000/docs | Interactive Swagger UI — try every endpoint! |
| http://127.0.0.1:8000/redoc | Clean, readable API documentation |
| http://127.0.0.1:8000/v1/patients | JSON list of all patients |

> **Tip:** The Swagger UI at `/docs` lets you click "Try it out" on any
> endpoint and send real requests.  This is one of the best features of
> FastAPI — you get interactive docs for free.

---

## Try These Requests

You can use the Swagger UI, `curl`, or any HTTP client (Thunder Client
in VS Code is great).

### List all patients
```bash
curl http://127.0.0.1:8000/v1/patients
```

### Filter by condition
```bash
curl "http://127.0.0.1:8000/v1/patients?condition=asthma"
```

### Create a new patient
```bash
curl -X POST http://127.0.0.1:8000/v1/patients \
  -H "Content-Type: application/json" \
  -d '{"name": "David Lee", "age": 65, "condition": "COPD"}'
```
Notice the response is `201 Created` — not `200 OK`.

### Get a specific patient (use an ID from the list)
```bash
curl http://127.0.0.1:8000/v1/patients/<paste-id-here>
```

### Delete a patient
```bash
curl -X DELETE http://127.0.0.1:8000/v1/patients/<paste-id-here>
```
Notice the response is `204 No Content` — the patient is gone, nothing
to return.

### Try a patient that doesn't exist
```bash
curl http://127.0.0.1:8000/v1/patients/nonexistent-id
```
You should get `404 Not Found`.

---

## Code Walkthrough

Open [app.py](app.py) and read through the comments.  Key things to
notice:

1. **Every endpoint has the correct status code** — `201` for POST,
   `204` for DELETE, `404` for missing resources.
2. **Pydantic models validate input** — if someone sends `{"age": -5}`,
   FastAPI returns `422` automatically.
3. **Query params handle filtering and pagination** — the list endpoint
   supports `?condition=X&limit=10&offset=0`.
4. **Path params identify specific resources** — `/v1/patients/{id}`.
5. **Response envelope** — every response uses `{data: ..., meta: ...}`
   for consistency.

---

## 🎯 Challenges

See the YOUR TURN section at the bottom of [app.py](app.py):

1. **(Easy)** Add a `GET /v1/patients/count` endpoint
2. **(Medium)** Add a `min_age` query parameter to the list endpoint
3. **(Stretch)** Add a `POST /v1/patients/search` endpoint — see
   [solutions/lab_01_challenge3.md](../solutions/lab_01_challenge3.md)

---

## ✅ Done When

- [ ] Your server is running and you can see the Swagger docs at `/docs`
- [ ] You have tried all 5 HTTP verbs (GET, POST, PUT, PATCH, DELETE)
- [ ] You got a `201` from POST, `204` from DELETE, `404` from a missing ID
- [ ] You understand the difference between path params and query params
- [ ] You attempted at least one challenge

---

**Next →** [Lab 02: Train the Model](../lab_02_train_model/README.md)
