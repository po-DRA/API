# Lab 04: Test the API

> **Goal:** Write automated tests for the prediction API using pytest
> and FastAPI's TestClient.

> **Time:** ~25 minutes

> **Prerequisites:**
> [Lab 03: Expose the Model](../lab_03_expose_model/README.md)

---

## What You'll Learn

- How to use FastAPI's TestClient (no server needed!)
- How to test every HTTP verb and status code
- How to validate response shapes
- How to skip tests gracefully when the model isn't available

---

## Why Test an API?

1. **Catch bugs before deployment.** A broken endpoint in production
   could affect clinical workflows.
2. **Verify REST conventions.** Did you return 201 for POST? 204 for
   DELETE? Tests enforce this.
3. **Tests ARE documentation.** A new team member can read the tests
   to understand exactly what each endpoint does.
4. **Refactor with confidence.** Change the code, run the tests, know
   nothing is broken.

---

## Run the Tests

```bash
# Go back to the project root (if you're still in lab_03)
cd ..

# Run the tests
pytest lab_04_test_api/test_api.py -v
```

The `-v` flag shows each test name and its result.

Expected output (if model is trained):
```
test_create_prediction_returns_201          PASSED
test_create_prediction_returns_data_envelope PASSED
test_empty_note_returns_422                 PASSED
test_get_nonexistent_returns_404            PASSED
test_delete_existing_returns_204            PASSED
...
```

If the model is not trained, model-dependent tests are **skipped**
(not failed):
```
test_create_prediction_returns_201          SKIPPED (Model not trained)
```

---

## What the Tests Cover

| Category | What's Tested | Expected Code |
|---|---|---|
| **POST** | Create prediction | 201 |
| **POST** | Missing note field | 422 |
| **POST** | Note too short | 422 |
| **GET** | List predictions | 200 |
| **GET** | Empty list | 200 (not 404!) |
| **GET** | Filter by label | 200 |
| **GET** | Pagination | 200 |
| **GET** | Specific prediction | 200 |
| **GET** | Nonexistent prediction | 404 |
| **DELETE** | Remove prediction | 204 |
| **DELETE** | Nonexistent prediction | 404 |
| **Model info** | Metadata endpoint | 200 |

---

## Code Walkthrough

Open [test_api.py](test_api.py) and notice:

1. **TestClient** lets you test without starting a real server.
   It simulates HTTP requests in-process.

2. **`clear_predictions` fixture** resets the database before each
   test so tests don't depend on each other.

3. **`skip_without_model`** - tests that need the model are skipped
   (not failed) if the model isn't trained yet.

4. **Class-based grouping** - tests are organized by HTTP verb for
   readability.

---

## 🎯 Challenges

See the YOUR TURN section at the bottom of [test_api.py](test_api.py):

1. **(Easy)** Test that total count is correct after creating 5 predictions
2. **(Medium)** Test double-delete behavior
3. **(Stretch)** Parameterized test for multiple clinical notes

---

## ✅ Done When

- [ ] All tests pass (or skip gracefully if model not trained)
- [ ] You understand what each test is checking
- [ ] You can explain why an empty list returns 200, not 404
- [ ] You attempted at least one challenge

---

**Next →** [Lab 05: Deploy](../lab_05_deploy/README.md)
