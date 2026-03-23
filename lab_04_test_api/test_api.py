"""
Lab 04 — Test the REST API with pytest
=======================================
Automated tests for the prediction API using FastAPI's TestClient.

How to run:
    pytest lab_04_test_api/test_api.py -v

What this tests:
    - All HTTP verbs (GET, POST, DELETE)
    - Correct status codes (200, 201, 204, 404, 422)
    - Response shape validation ({data: ..., meta: ...})
    - Filtering and pagination
    - Graceful handling when model is not loaded

Why test an API?
    - Catch bugs before deployment
    - Verify REST conventions (correct status codes!)
    - Document expected behavior (tests ARE documentation)
    - Enable confident refactoring later

Reference:
    - FastAPI testing docs: https://fastapi.tiangolo.com/tutorial/testing/
    - pytest docs: https://docs.pytest.org/
"""

import os

import pytest
from fastapi.testclient import TestClient

# ── Import the app ──────────────────────────────────────────────────
# We import from lab_03 because that's the full prediction API.
from lab_03_expose_model.app import MODEL_PATH, app, predictions_db

# ── Helper ──────────────────────────────────────────────────────────
# Some tests need the ML model loaded.  If it's not available (e.g.
# the learner hasn't trained it yet), we skip those tests gracefully
# instead of failing with a confusing error.
#
# We check if the model FILE exists (not the in-memory variable)
# because the model is loaded at app startup via the lifespan context,
# which only runs when the TestClient is used.

MODEL_LOADED = os.path.exists(MODEL_PATH)
skip_without_model = pytest.mark.skipif(
    not MODEL_LOADED,
    reason="Model not trained yet — run 'python lab_02_train_model/train.py'",
)


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def client():
    """Create a TestClient with lifespan support.

    Using TestClient as a context manager ensures the lifespan runs,
    which loads the ML model at startup and cleans up on shutdown.
    The 'module' scope means this runs once for all tests in this file.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_predictions():
    """Clear the predictions database before each test.

    This ensures tests are independent — one test's predictions
    don't leak into another test.
    """
    predictions_db.clear()
    yield
    predictions_db.clear()


# =====================================================================
#  Tests for POST /v1/predictions
# =====================================================================


@skip_without_model
class TestCreatePrediction:
    """Tests for creating predictions (POST)."""

    def test_create_prediction_returns_201(self, client):
        """POST should return 201 Created — the correct REST status
        code for creating a new resource."""
        response = client.post(
            "/v1/predictions",
            json={"note": "Patient has acute chest pain with ST elevation on ECG"},
        )
        assert response.status_code == 201

    def test_create_prediction_returns_data_envelope(self, client):
        """Response must use our standard {data: ..., meta: ...} envelope."""
        response = client.post(
            "/v1/predictions",
            json={"note": "Routine annual physical. All vitals within normal limits."},
        )
        body = response.json()
        assert "data" in body
        assert "meta" in body

    def test_create_prediction_has_required_fields(self, client):
        """The prediction record must include id, note, prediction,
        confidence, and created_at."""
        response = client.post(
            "/v1/predictions",
            json={"note": "Patient found unresponsive with GCS of 3. Emergency intubation needed."},
        )
        data = response.json()["data"]
        assert "id" in data
        assert "note" in data
        assert "prediction" in data
        assert "confidence" in data
        assert "created_at" in data

    def test_prediction_is_urgent_or_routine(self, client):
        """Model should return one of the two known labels."""
        response = client.post(
            "/v1/predictions",
            json={"note": "Massive upper GI hemorrhage. Hemoglobin dropping rapidly."},
        )
        prediction = response.json()["data"]["prediction"]
        assert prediction in ("urgent", "routine")

    def test_confidence_is_between_0_and_1(self, client):
        """Confidence score must be a probability (0 to 1)."""
        response = client.post(
            "/v1/predictions",
            json={"note": "Follow-up for well-controlled diabetes. HbA1c stable."},
        )
        confidence = response.json()["data"]["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_empty_note_returns_422(self, client):
        """Sending a note that is too short should return 422
        Unprocessable Entity — FastAPI validates this automatically
        because we set min_length=10 on the Pydantic model."""
        response = client.post(
            "/v1/predictions",
            json={"note": "short"},
        )
        assert response.status_code == 422

    def test_missing_note_returns_422(self, client):
        """Sending no note at all should return 422."""
        response = client.post("/v1/predictions", json={})
        assert response.status_code == 422


# =====================================================================
#  Tests for GET /v1/predictions
# =====================================================================


@skip_without_model
class TestListPredictions:
    """Tests for listing predictions (GET)."""

    def test_empty_list_returns_200(self, client):
        """An empty collection should return 200 with an empty list —
        not 404.  An empty list IS a valid response."""
        response = client.get("/v1/predictions")
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_list_returns_created_predictions(self, client):
        """After creating predictions, the list should include them."""
        # Create two predictions
        client.post(
            "/v1/predictions",
            json={"note": "Acute respiratory distress. SpO2 falling rapidly."},
        )
        client.post(
            "/v1/predictions",
            json={"note": "Routine prenatal visit. Fetal heart tones normal."},
        )
        response = client.get("/v1/predictions")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 2

    def test_filter_by_prediction_label(self, client):
        """Query param ?prediction=urgent should filter results."""
        # Create one of each
        client.post(
            "/v1/predictions",
            json={"note": "Acute chest pain with troponin elevation and diaphoresis."},
        )
        client.post(
            "/v1/predictions",
            json={"note": "Routine well-child visit. Growth on track. Immunizations current."},
        )
        response = client.get("/v1/predictions?prediction=urgent")
        assert response.status_code == 200
        for item in response.json()["data"]:
            assert item["prediction"] == "urgent"

    def test_pagination_with_limit_and_offset(self, client):
        """limit and offset should control pagination."""
        # Create 3 predictions
        for note in [
            "Emergency: massive hemorrhage requiring immediate intervention.",
            "Routine follow-up for managed hypothyroidism. TSH normal.",
            "Status epilepticus. Benzodiazepines administered without effect.",
        ]:
            client.post("/v1/predictions", json={"note": note})

        # Get first 2
        response = client.get("/v1/predictions?limit=2&offset=0")
        assert len(response.json()["data"]) == 2

        # Get the third
        response = client.get("/v1/predictions?limit=2&offset=2")
        assert len(response.json()["data"]) == 1

    def test_meta_includes_total_count(self, client):
        """The meta section should include the total count for
        pagination UI."""
        client.post(
            "/v1/predictions",
            json={"note": "Patient presenting with acute abdomen and rebound tenderness."},
        )
        response = client.get("/v1/predictions")
        meta = response.json()["meta"]
        assert "total" in meta
        assert meta["total"] == 1


# =====================================================================
#  Tests for GET /v1/predictions/{id}
# =====================================================================


@skip_without_model
class TestGetPrediction:
    """Tests for getting a specific prediction (GET by ID)."""

    def test_get_existing_returns_200(self, client):
        """Getting a prediction that exists should return 200."""
        create = client.post(
            "/v1/predictions",
            json={"note": "Suspected pulmonary embolism with acute dyspnea and pleuritic pain."},
        )
        pred_id = create.json()["data"]["id"]

        response = client.get(f"/v1/predictions/{pred_id}")
        assert response.status_code == 200
        assert response.json()["data"]["id"] == pred_id

    def test_get_nonexistent_returns_404(self, client):
        """Getting a prediction that doesn't exist should return 404 —
        the correct REST response for 'resource not found'."""
        response = client.get("/v1/predictions/nonexistent-id")
        assert response.status_code == 404


# =====================================================================
#  Tests for DELETE /v1/predictions/{id}
# =====================================================================


@skip_without_model
class TestDeletePrediction:
    """Tests for deleting predictions (DELETE)."""

    def test_delete_existing_returns_204(self, client):
        """DELETE should return 204 No Content — the resource is gone,
        there's nothing to send back."""
        create = client.post(
            "/v1/predictions",
            json={"note": "DKA with blood glucose 580 and pH 7.1. Insulin drip started."},
        )
        pred_id = create.json()["data"]["id"]

        response = client.delete(f"/v1/predictions/{pred_id}")
        assert response.status_code == 204

    def test_delete_nonexistent_returns_404(self, client):
        """Trying to delete something that doesn't exist returns 404."""
        response = client.delete("/v1/predictions/nonexistent-id")
        assert response.status_code == 404

    def test_delete_actually_removes_prediction(self, client):
        """After deleting, the prediction should no longer be found."""
        create = client.post(
            "/v1/predictions",
            json={
                "note": "New onset atrial fibrillation with rapid ventricular response at 180 bpm."
            },
        )
        pred_id = create.json()["data"]["id"]

        client.delete(f"/v1/predictions/{pred_id}")

        # Verify it's gone
        response = client.get(f"/v1/predictions/{pred_id}")
        assert response.status_code == 404


# =====================================================================
#  Tests for GET /v1/model/info
# =====================================================================


class TestModelInfo:
    """Tests for the model info endpoint."""

    @skip_without_model
    def test_model_info_returns_200(self, client):
        """When model is loaded, info should return 200."""
        response = client.get("/v1/model/info")
        assert response.status_code == 200

    @skip_without_model
    def test_model_info_has_accuracy(self, client):
        """Model info should include accuracy from training."""
        response = client.get("/v1/model/info")
        data = response.json()["data"]
        assert "accuracy" in data


# =====================================================================
#  YOUR TURN — Add Your Own Tests
# =====================================================================
#
# Challenge 1 (Easy):
#   Write a test that creates 5 predictions and verifies the total
#   count in the meta is correct.
#
# Challenge 2 (Medium):
#   Write a test for double-delete: delete a prediction, then try to
#   delete it again. What status code should the second delete return?
#
# Challenge 3 (Stretch):
#   Write a parameterized test (using @pytest.mark.parametrize) that
#   tests multiple clinical notes and verifies:
#     - All urgent-sounding notes get "urgent"
#     - All routine-sounding notes get "routine"
#   This is a great way to build a test suite for your model!
