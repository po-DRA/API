# Lab 00 — Quiz Answers

1. **GET** — retrieving data always uses GET.

2. **201 Created** — POST that creates a new resource should return 201,
   not 200.

3. **204 No Content** — the resource is gone; there is nothing to send
   back.

4. Two problems:
   - It uses a verb (`get`) — the HTTP method already says GET.
   - It mixes filtering into the path — it should be
     `GET /v1/patients?status=active`.

5. **404 Not Found** — the resource does not exist.

6. **Path parameter** — identifies a specific resource:
   `/v1/patients/42` (patient with ID 42).
   **Query parameter** — filters or paginates a collection:
   `/v1/patients?status=active` (only active patients).

7. Statelessness means every request carries all the information the
   server needs.  This lets you run multiple copies of the server
   behind a load balancer — any copy can handle any request because
   none of them need to "remember" previous requests.

8. Any two of:
   - Non-Python users (JavaScript, mobile apps) can call an API but
     can't `pip install`.
   - You deploy once and everyone gets the latest version instantly —
     no asking every user to upgrade.
   - You can add access control (API keys, rate limits, audit logs).
   - Data stays on the server, so you control security and compliance.

9. The JSON was syntactically valid, but the *values* didn't make
   sense (e.g. a negative age, or a missing required field).  It's a
   **client error** — the server understood the shape but not the
   content.

10. Any two of:
    - Interactive Swagger UI (`/docs`)
    - ReDoc documentation (`/redoc`)
    - The raw OpenAPI JSON spec (`/openapi.json`)
    - Client code generation
