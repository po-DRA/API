# Lab 05 Challenge Solutions

## Challenge 1: Enable Auto-Deploy

On Render: **Settings > Build & Deploy > Auto-Deploy > Yes**.

That's it! Now every `git push origin main` triggers a build.

---

## Challenge 2: GitHub Actions CI Pipeline

Create the file `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Train model (needed for Lab 04 tests)
        run: uv run python lab_02_train_model/train.py

      - name: Run tests
        run: uv run pytest -m "not llm_eval" -v
```

**What this does:**
- Triggers on every push to `main` and on pull requests
- Sets up Python 3.11 and installs `uv`
- Installs all dependencies (including dev/test deps)
- Trains the model (Lab 04 tests need it)
- Runs all tests except live LLM evals (those need an API key)

---

## Challenge 3: Add Linting

Add a linting step to the same workflow, after the test step:

```yaml
      - name: Lint with ruff
        run: uv run ruff check .
```

This catches style issues and common bugs before they reach production.
If you want to go further, you can also add:

```yaml
      - name: Check formatting
        run: uv run ruff format --check .
```

This fails the build if any file isn't properly formatted.
