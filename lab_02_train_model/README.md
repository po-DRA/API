# Lab 02: Train the Model

> **Goal:** Train a clinical urgency classifier that you will expose as
> a REST API in the next lab.

> **Time:** ~20 minutes

> **Prerequisites:** [Lab 01: Your First API](../lab_01_your_first_api/README.md)

---

## What You'll Learn

- How to build a scikit-learn Pipeline (TF-IDF + Logistic Regression)
- Why Pipelines are better than separate fit/transform steps
- How to save a trained model with joblib
- How to sanity-check predictions before deploying

---

## The Data

[data/clinical_notes.csv](../data/clinical_notes.csv) contains 30
labelled clinical notes:

| label | count | examples |
|---|---|---|
| `urgent` | 10 | chest pain, GI hemorrhage, status epilepticus |
| `routine` | 20 | annual physical, follow-up, medication refill |

Each row has a `note` (free-text clinical note) and a `label`
(`urgent` or `routine`).

> **Note:** This is a tiny dataset for teaching purposes.  In a real
> project you'd have thousands of notes and would want to address class
> imbalance more carefully.

---

## Run It

```bash
# First, go back to the project root (if you're still in lab_01)
cd ..

# Run the training script
python lab_02_train_model/train.py
```

You should see output like:

```
📂 Loading data from .../data/clinical_notes.csv
   Loaded 30 notes  ({'routine': 20, 'urgent': 10})
   Train: 24 notes | Test: 6 notes
🏋️ Training pipeline...
📊 Test Accuracy: 100.00%
💾 Model saved to .../models/urgency_classifier.joblib
📋 Metadata saved to .../models/model_meta.json
🔍 Sanity-check predictions:
   [ urgent]  Patient has acute chest pain and ST-elevation. Troponin rising...
   [routine]  Routine annual check-up. All vitals within normal limits...
✅ Training complete!
```

---

## What Just Happened?

1. **Loaded** `clinical_notes.csv` into a DataFrame
2. **Split** into 80% train / 20% test (stratified by label)
3. **Built a Pipeline** with:
   - `TfidfVectorizer` - converts text to numerical TF-IDF features
   - `LogisticRegression` - classifies based on those features
4. **Trained** the pipeline on the training set
5. **Evaluated** on the held-out test set
6. **Saved** the pipeline to `models/urgency_classifier.joblib`
7. **Saved metadata** to `models/model_meta.json`
8. **Ran sanity checks** on a few hand-crafted notes

### Why a Pipeline?

Read the detailed explanation in [train.py](train.py).  The short
version: a Pipeline bundles TF-IDF and the classifier into one object
so you can't accidentally forget a preprocessing step when making
predictions later.

---

## Connection to the ci-cd-template

If you completed the [ci-cd-template tutorial](https://github.com/po-DRA/ci-cd-template),
you already trained a model using a similar pattern.  The key
difference here is that we are training the model so we can **serve it
as an API**, not just use it in a notebook.

The training script is inspired by:
[ci-cd-template/scripts/train.py](https://github.com/po-DRA/ci-cd-template/blob/main/scripts/train.py)

---

## 🎯 Challenges

1. **(Easy)** Open `models/model_meta.json` and inspect it.  What
   accuracy did you get?
2. **(Medium)** Add 5 more clinical notes to `clinical_notes.csv`
   and retrain.  Does the accuracy change?
3. **(Stretch)** Modify `train.py` to also save a confusion matrix
   as `models/confusion_matrix.json`.

---

## ✅ Done When

- [ ] `models/urgency_classifier.joblib` exists
- [ ] `models/model_meta.json` exists and looks correct
- [ ] The sanity-check predictions make medical sense
- [ ] You understand why we use a Pipeline

---

**Next →** [Lab 03: Expose the Model as an API](../lab_03_expose_model/README.md)
