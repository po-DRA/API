# Lab 04 — Challenge Solutions

## Challenge 1 (Easy): Test total count after creating 5 predictions

```python
@skip_without_model
def test_total_count_after_five_predictions(client):
    """Create 5 predictions and verify the total count in meta."""
    notes = [
        "Acute chest pain with ST-elevation and troponin rise.",
        "Routine follow-up for managed hypertension. BP stable.",
        "Severe sepsis with lactate 4.2. Blood cultures drawn.",
        "Annual wellness visit. No complaints. Vitals normal.",
        "Status epilepticus not responding to first-line treatment.",
    ]
    for note in notes:
        client.post("/v1/predictions", json={"note": note})

    response = client.get("/v1/predictions")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 5
    assert len(response.json()["data"]) == 5
```

---

## Challenge 2 (Medium): Test double-delete behavior

The second DELETE should return **404** — the resource no longer exists.

```python
@skip_without_model
def test_double_delete_returns_404(client):
    """Deleting a prediction twice: first returns 204, second returns 404."""
    # Create a prediction
    create = client.post(
        "/v1/predictions",
        json={"note": "Acute respiratory failure requiring emergency intubation."},
    )
    pred_id = create.json()["data"]["id"]

    # First delete — should succeed
    response = client.delete(f"/v1/predictions/{pred_id}")
    assert response.status_code == 204

    # Second delete — resource is already gone
    response = client.delete(f"/v1/predictions/{pred_id}")
    assert response.status_code == 404
```

> **Why 404?** After the first DELETE, the resource no longer exists.
> Any subsequent request for that resource — whether GET or DELETE —
> should return 404 Not Found. This is idiomatic REST behavior.

---

## Challenge 3 (Stretch): Parameterized test for multiple notes

```python
@skip_without_model
@pytest.mark.parametrize(
    "note, expected_label",
    [
        ("Acute MI with ST-elevation. Troponin critically elevated. Cath lab activated.", "urgent"),
        ("Massive GI hemorrhage with hemoglobin of 4.2. Transfusion started.", "urgent"),
        ("Patient in anaphylactic shock after bee sting. Epinephrine administered.", "urgent"),
        ("Routine annual physical. All vitals within normal limits.", "routine"),
        ("Follow-up for well-controlled diabetes. HbA1c stable at 6.2.", "routine"),
        ("Routine prenatal visit at 28 weeks. Fetal heart tones normal.", "routine"),
    ],
)
def test_prediction_matches_expected_label(client, note, expected_label):
    """Verify the model predicts the expected label for known notes."""
    response = client.post("/v1/predictions", json={"note": note})
    assert response.status_code == 201
    assert response.json()["data"]["prediction"] == expected_label
```

> **Note:** This test depends on the model's accuracy. With our small
> training dataset (35 samples), some edge-case notes may be
> misclassified. Use notes with strong signal words from the training
> data for reliable results.

Usage:
```bash
pytest lab_04_test_api/test_api.py -v
```
