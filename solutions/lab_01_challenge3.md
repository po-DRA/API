# Lab 01 — Challenge 3: Search Endpoint

## Why POST for Search?

HTTP GET requests **should not have a request body** (some servers
ignore it).  When the search criteria are too complex for query
parameters (e.g. nested filters, free-text queries), using POST with a
JSON body is a common REST pattern.

## Solution

```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, example="diabetes")


@app.post("/v1/patients/search", status_code=200, tags=["Patients"])
def search_patients(search: SearchRequest):
    """Search patients by name or condition (case-insensitive)."""
    q = search.query.lower()
    results = [
        p for p in patients_db.values()
        if q in p["name"].lower() or q in p["condition"].lower()
    ]
    return {"data": results, "meta": {"total": len(results)}}
```

Note: We return `200 OK` (not `201`) because we are not *creating*
anything — we are performing a search that returns results.
