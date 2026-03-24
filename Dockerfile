# ============================================================
# Dockerfile — REST-API-Builder
# ============================================================
# This Dockerfile does three things:
#   1. Installs Python dependencies
#   2. Trains the ML model at BUILD time (so it's baked into the image)
#   3. Runs the production FastAPI server
#
# Works with:
#   - HuggingFace Spaces (port 7860)
#   - Any Docker host (docker run -p 7860:7860)
#
# Build & run locally:
#   docker build -t rest-api-builder .
#   docker run -p 7860:7860 rest-api-builder
# ============================================================

FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install uv — a fast Python package manager written in Rust
RUN pip install --no-cache-dir uv

# Copy dependency files first (Docker caches this layer if deps don't change)
COPY pyproject.toml .

# Copy the entire project
COPY . .

# Install dependencies using uv
RUN uv sync --no-dev

# Use the venv for all subsequent commands
ENV PATH="/app/.venv/bin:$PATH"

# Train the model at build time so it's ready when the container starts
RUN python lab_02_train_model/train.py

# Default port: 7860 for HuggingFace Spaces, overridden by $PORT on Render
ENV PORT=7860
EXPOSE 7860

# Run the production-ready app (uses $PORT so it works on both Render and HF Spaces)
CMD uvicorn lab_05_deploy.app:app --host 0.0.0.0 --port $PORT
