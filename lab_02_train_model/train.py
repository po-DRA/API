"""
Lab 02 — Train a Clinical Urgency Classifier
=============================================
This script trains a machine learning model that classifies clinical
notes as "urgent" or "routine".

It uses:
  - TF-IDF to convert text into numbers (bag-of-words on steroids)
  - Logistic Regression to classify the notes
  - A scikit-learn Pipeline to bundle both steps together

How to run:
    python lab_02_train_model/train.py

After running you will find:
    models/urgency_classifier.joblib   ← the trained pipeline
    models/model_meta.json             ← accuracy, date, class labels

Why a Pipeline?
    A Pipeline chains preprocessing (TF-IDF) and the classifier into a
    single object. This means:
    1. You can't accidentally forget to transform new data
    2. You save/load ONE object instead of two
    3. Cross-validation and grid search work out of the box
    It's the recommended scikit-learn pattern for any text classifier.

Reference:
    Training script inspiration:
        https://github.com/po-DRA/ci-cd-template/blob/main/scripts/train.py
    Deploying ML models with FastAPI:
        https://www.analyticsvidhya.com/blog/2022/09/deploying-ml-models-using-fastapi/
"""

import json
import os
from datetime import UTC, datetime

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# ── Paths ───────────────────────────────────────────────────────────
# We use os.path so this script works from any working directory.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "clinical_notes.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "urgency_classifier.joblib")
META_PATH = os.path.join(MODEL_DIR, "model_meta.json")


def train():
    """Train the urgency classifier and save it to disk."""

    # ── 1. Load the data ────────────────────────────────────────────
    print("[LOAD] Loading data from", DATA_PATH)
    df = pd.read_csv(DATA_PATH)
    print(f"   Loaded {len(df)} notes  ({df['label'].value_counts().to_dict()})")

    X = df["note"]  # The clinical note text
    y = df["label"]  # "urgent" or "routine"

    # ── 2. Split into train / test ──────────────────────────────────
    # We hold out 20% of the data to check how well the model
    # generalises to notes it has never seen.
    # stratify=y ensures both sets have the same ratio of urgent/routine.
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,  # reproducible split
        stratify=y,  # keep class balance
    )
    print(f"   Train: {len(X_train)} notes | Test: {len(X_test)} notes")

    # ── 3. Build the Pipeline ───────────────────────────────────────
    # Why a Pipeline?
    #   - TfidfVectorizer converts text → sparse matrix of TF-IDF features.
    #     TF-IDF stands for Term Frequency–Inverse Document Frequency.
    #     It rewards words that are frequent in one document but rare
    #     across all documents (i.e., distinctive words).
    #   - LogisticRegression learns which TF-IDF features predict
    #     "urgent" vs "routine".
    #   - Wrapping them in a Pipeline means we call .fit() and .predict()
    #     once, and scikit-learn handles the transformations internally.
    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=5000,  # keep the top 5000 words
                    ngram_range=(1, 2),  # use single words AND two-word phrases
                    stop_words="english",  # drop common words like "the", "is"
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,  # enough iterations to converge
                    class_weight="balanced",  # handle class imbalance (fewer urgent than routine)
                    random_state=42,
                ),
            ),
        ]
    )

    # ── 4. Train the model ──────────────────────────────────────────
    print("[TRAIN] Training pipeline...")
    pipeline.fit(X_train, y_train)

    # ── 5. Evaluate on the test set ─────────────────────────────────
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, zero_division=0)

    print(f"\n[EVAL] Test Accuracy: {accuracy:.2%}")
    print(report)

    # ── 6. Save the model ──────────────────────────────────────────
    os.makedirs(MODEL_DIR, exist_ok=True)

    # joblib is the recommended way to serialise scikit-learn models.
    # It handles numpy arrays and sparse matrices efficiently.
    joblib.dump(pipeline, MODEL_PATH)
    print(f"[SAVE] Model saved to {MODEL_PATH}")

    # Save metadata so the API can report model info without loading
    # the full pipeline into memory just to answer "what version is this?"
    meta = {
        "model_type": "TF-IDF + Logistic Regression Pipeline",
        "accuracy": round(accuracy, 4),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "classes": list(pipeline.classes_),
        "n_features": pipeline.named_steps["tfidf"].max_features,
        "trained_at": datetime.now(UTC).isoformat(),
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[META] Metadata saved to {META_PATH}")

    # ── 7. Sanity check — try some predictions ─────────────────────
    # These quick checks let you confirm the model "makes sense"
    # before you wire it up as an API.
    print("\n[CHECK] Sanity-check predictions:")
    test_notes = [
        "Patient has acute chest pain and ST-elevation. Troponin rising.",
        "Routine annual check-up. All vitals within normal limits.",
        "Massive GI bleed, hemoglobin dropping rapidly. Transfusion needed.",
        "Follow-up for well-controlled hypertension. Continue current meds.",
    ]
    predictions = pipeline.predict(test_notes)
    for note, pred in zip(test_notes, predictions, strict=True):
        print(f"   [{pred:>7s}]  {note[:70]}...")

    print("\n[DONE] Training complete!")


if __name__ == "__main__":
    train()
