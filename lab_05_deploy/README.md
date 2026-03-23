# Lab 05 — Deploy Your API

> **Goal:** Deploy the prediction API so anyone on the internet can
> use it.  Three options: Render, HuggingFace Spaces, or Docker.

> **Time:** ~30 minutes

> **Prerequisites:**
> [Lab 04 — Test the API](../lab_04_test_api/README.md)

---

## What You'll Learn

- How to deploy a FastAPI app to Render (free tier)
- How to deploy to HuggingFace Spaces via Docker
- How to run the API in Docker locally
- What CORS is and why it matters
- What a health check endpoint does

---

## Before You Start

Make sure you are in the **project root** directory (not inside a lab folder):

```bash
# Go back to the project root if needed
cd ..
```

---

## What's Different in the Production App?

Open [app.py](app.py) and compare it to Lab 03's version.  Key additions:

| Feature | Why It Matters |
|---|---|
| **CORS middleware** | Lets browsers (React, dashboards) call your API |
| **Demo mode** | API works even without a trained model — returns placeholder predictions |
| **Health check** (`/health`) | Hosting platforms ping this to know if your service is alive |
| **Root endpoint** (`/`) | Friendly landing page with links to docs |

---

## Option A: Deploy to Render (Recommended for Beginners)

[Render](https://render.com) is a cloud platform with a free tier —
perfect for learning.

### Steps

1. **Push your code to GitHub** (if you haven't already):
   ```bash
   git add -A
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Go to** [render.com](https://render.com) and sign in with GitHub.

3. **Click "New +" → "Web Service"**.

4. **Connect your GitHub repo** (REST-API-Builder or API).

5. Render will detect `render.yaml` automatically.  Verify these
   settings:
   - **Build command:** `pip install uv && uv sync && python lab_02_train_model/train.py`
   - **Start command:** `uvicorn lab_05_deploy.app:app --host 0.0.0.0 --port $PORT`

6. **Click "Create Web Service"** and wait for the build (~2 min).

7. **Visit your URL** — e.g. `https://your-app-name.onrender.com/docs`

> **Note:** The free tier spins down after 15 min of inactivity.
> The first request after idle takes ~30 seconds to cold-start.

### How render.yaml Works

The [render.yaml](../render.yaml) file is a blueprint that tells Render:
- **buildCommand** — install dependencies AND train the model
- **startCommand** — run the production app
- **plan: free** — use the free tier

---

## Option B: Deploy to HuggingFace Spaces

[HuggingFace Spaces](https://huggingface.co/spaces) hosts Docker-based
apps for free.

### Steps

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) →
   "Create new Space".

2. Choose **Docker** as the SDK.

3. Clone the Space repo locally and copy your project files into it.

4. The [Dockerfile](../Dockerfile) is already configured for HF Spaces:
   - Trains the model at build time
   - Exposes port 7860 (HF Spaces requirement)

5. Push to the Space and wait for the build.

6. Your API will be live at
   `https://huggingface.co/spaces/<your-username>/<space-name>`

---

## Option C: Run with Docker Locally

If you want to practice Docker before deploying, run the API in a
container on your own machine.

### Steps

```bash
# 1. Build the Docker image
#    This installs dependencies AND trains the model
docker build -t rest-api-builder .

# 2. Run the container
#    -p 7860:7860 maps container port to your machine
docker run -p 7860:7860 rest-api-builder

# 3. Visit the API
#    http://localhost:7860/docs
```

### What the Dockerfile Does

```dockerfile
FROM python:3.11-slim          # Start with a clean Python image
RUN pip install uv             # Install uv (fast package manager)
COPY pyproject.toml .          # Copy deps first (cached layer)
COPY . .                       # Copy all project files
RUN uv sync --no-dev           # Install production deps only
RUN python lab_02_train_model/train.py   # Train model at build time
EXPOSE 7860                    # Declare the port
CMD ["uvicorn", ...]           # Start the server
```

Key Docker concepts:
- **Image** — a snapshot of your app + all dependencies (like a template)
- **Container** — a running instance of an image (like a VM, but lighter)
- **Layer caching** — Docker reuses unchanged layers, so rebuilds are fast
- **EXPOSE** — documents the port; `-p` actually maps it

### Useful Docker Commands

```bash
# List running containers
docker ps

# Stop a container
docker stop <container-id>

# View container logs
docker logs <container-id>

# Remove the image (to rebuild from scratch)
docker rmi rest-api-builder
```

---

## Verify Your Deployment

Regardless of which option you chose, test these endpoints:

```bash
# Replace URL with your deployment URL
URL="http://localhost:7860"  # or your Render/HF URL

# Health check
curl $URL/health

# Interactive docs
# Open in browser: $URL/docs

# Create a prediction
curl -X POST $URL/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"note": "Acute chest pain with ST-elevation and troponin rise"}'

# List predictions
curl $URL/v1/predictions

# Model info
curl $URL/v1/model/info
```

---

## Understanding CORS

When you open a React dashboard at `http://localhost:3000` and it
tries to call your API at `http://localhost:7860`, the browser blocks
it by default.  This is **Cross-Origin Resource Sharing (CORS)**.

Our app.py adds CORS middleware that says "allow requests from
anywhere."  In production, you would restrict this to your actual
frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://my-dashboard.example.com"],
    ...
)
```

---

## ✅ Done When

- [ ] Your API is deployed and accessible via a public URL
  (OR running in Docker locally)
- [ ] The `/health` endpoint returns `{"status": "healthy"}`
- [ ] You can create a prediction via `/docs`
- [ ] You understand why CORS middleware is needed
- [ ] You can explain what the Dockerfile does step by step

---

## 🎉 Congratulations!

You've completed the entire REST-API-Builder tutorial!

Here's what you've accomplished:

1. **Lab 00** — Learned REST fundamentals, HTTP verbs, and status codes
2. **Lab 01** — Built your first CRUD API with FastAPI
3. **Lab 02** — Trained a clinical urgency classifier
4. **Lab 03** — Exposed the model as a REST API
5. **Lab 04** — Wrote automated tests with pytest
6. **Lab 05** — Deployed to the cloud (or Docker)

You now have the skills to take **any** machine learning model and
serve it as a production-ready REST API.

### What to Explore Next

- Add authentication (API keys or OAuth)
- Connect to a real database (PostgreSQL, MongoDB)
- Add logging and monitoring
- Try deploying with CI/CD (see the
  [ci-cd-template](https://github.com/po-DRA/ci-cd-template))
- Explore the [API Learning Roadmap](https://bytebytego.com/guides/the-ultimate-api-learning-roadmap/)
