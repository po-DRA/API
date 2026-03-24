# models/

This folder stores trained model artifacts. The files are generated
when you run `lab_02_train_model/train.py` and are **not** checked
into Git (see `.gitignore`).

After training you will see:

| File | What it is |
|---|---|
| `urgency_classifier.joblib` | The trained scikit-learn Pipeline (TF-IDF + Logistic Regression) |
| `model_meta.json` | Metadata: accuracy, training date, feature count, class labels |
