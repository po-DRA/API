# Lab 05: Deploy Your API

> **Goal:** Deploy the prediction API so anyone on the internet can
> use it.  Three options: Render, HuggingFace Spaces, or Docker.

> **Time:** ~30 minutes

> **Prerequisites:**
> [Lab 04: Test the API](../lab_04_test_api/README.md)

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
| **Demo mode** | API works even without a trained model; returns placeholder predictions |
| **Health check** (`/health`) | Hosting platforms ping this to know if your service is alive |
| **Root endpoint** (`/`) | Friendly landing page with links to docs |

---

## Option A: Deploy to Render (Recommended for Beginners)

[Render](https://render.com) is a cloud platform with a free tier,
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

7. **Visit your URL**, e.g. `https://your-app-name.onrender.com/docs`

> **Note:** The free tier spins down after 15 min of inactivity.
> The first request after idle takes ~30 seconds to cold-start.

### How render.yaml Works

The [render.yaml](../render.yaml) file is a blueprint that tells Render:
- **buildCommand:** install dependencies AND train the model
- **startCommand:** run the production app
- **plan: free:** use the free tier

---

## Option B: Deploy to HuggingFace Spaces

[HuggingFace Spaces](https://huggingface.co/spaces) hosts Docker-based
apps for free.

### Steps

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) →
   "Create new Space".

2. Choose **Docker** as the SDK, select **Blank** template, and
   **CPU Basic** (free).

3. Add the HF Space as a second git remote (no need to clone a
   separate repo):
   ```bash
   # Add HF Space as a remote (one-time setup)
   git remote add hf https://huggingface.co/spaces/<your-username>/<space-name>

   # Push your code to the Space
   # You'll need a HuggingFace token with write permissions
   git push https://<your-username>:<your-hf-token>@huggingface.co/spaces/<your-username>/<space-name> main --force
   ```
   Use `--force` on the first push to overwrite the Space's default README.

4. The [Dockerfile](../Dockerfile) is already configured for HF Spaces:
   - Trains the model at build time
   - Exposes port 7860 (HF Spaces requirement)

5. Wait for the build (check the **Logs** tab on your Space page).

6. Find your Space URL. HuggingFace gives you **two different URLs** and
   this trips people up:

   | URL | What you see |
   |---|---|
   | `https://huggingface.co/spaces/<username>/<space-name>` | The HF Space page - shows the raw API JSON, no docs |
   | `https://<username>-<space-name>.hf.space/docs` | Your actual Swagger docs |

   The second URL is the one you want. The pattern is:
   - replace `/` between username and space name with `-`
   - add `.hf.space` at the end

   **Example:** if your username is `priyanka-nl` and space name is `testbed`:
   - Space page: `https://huggingface.co/spaces/priyanka-nl/testbed`
   - Swagger docs: `https://priyanka-nl-testbed.hf.space/docs`
   - Playground: `https://priyanka-nl-testbed.hf.space/play`

> **Tip:** Bookmark the `hf.space` URL — that's your API's public address.

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
- **Image** - a snapshot of your app + all dependencies (like a template)
- **Container** - a running instance of an image (like a VM, but lighter)
- **Layer caching** - Docker reuses unchanged layers, so rebuilds are fast
- **EXPOSE** - documents the port; `-p` actually maps it

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

## Auto-Deploy on Push

When you connect Render (or HuggingFace Spaces) to your GitHub repo,
it can **automatically redeploy** every time you push to `main`. No
manual button clicks needed.

On Render, check: **Settings > Build & Deploy > Auto-Deploy** and make
sure it's set to **"Yes"**. Now every `git push` triggers a new build
and deploy automatically.

This is the simplest form of **Continuous Deployment (CD)**. For a more
robust setup, you'd add a CI pipeline that runs tests *before* deploying
(see Challenge 2 below).

---

## Challenges

1. **(Easy)** Enable auto-deploy on Render so that every push to `main`
   triggers a new deployment automatically. Verify it works by making
   a small change, pushing, and watching the build start on its own.

2. **(Medium)** Set up a GitHub Actions CI pipeline that runs your
   tests on every push. Create a `.github/workflows/ci.yml` file that:
   - Installs dependencies with `uv`
   - Runs `pytest` on Lab 04 and Lab 06 tests
   - Hint: you'll need `actions/checkout`, `actions/setup-python`,
     and a step to install `uv`

3. **(Stretch)** Extend your CI pipeline to also run `ruff check .`
   so linting errors are caught before they reach production.

See [solutions/lab_05_challenges.md](../solutions/lab_05_challenges.md)
for answers.

---

## ✅ Done When

- [ ] Your API is deployed and accessible via a public URL
  (OR running in Docker locally)
- [ ] The `/health` endpoint returns `{"status": "healthy"}`
- [ ] You can create a prediction via `/docs`
- [ ] You understand why CORS middleware is needed
- [ ] You can explain what the Dockerfile does step by step

---

**Next →** [Lab 06: LLM API](../lab_06_llm_api/README.md)
