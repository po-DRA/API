# 🧠 Step 0 — What Is an API, and Why Does a Researcher Need One?

> ⏱ **Time: ~10 minutes** | No code yet — just the mental model.

---

## The One Analogy You Need

Imagine you're a lab technician. You don't need to know how an MRI machine is built — you just put a patient in, press a button, and get results back.

**An API is that button.**

An API (**A**pplication **P**rogramming **I**nterface) is a contract between:
- A **caller** — the one asking for something ("classify this clinical note")
- A **service** — the one doing the work (your ML model)

The caller doesn't care *how* the model works internally. It just sends a request and gets an answer.

---

## Why Wrap an ML Model in an API?

| Without an API | With an API |
|---|---|
| Run a Python script manually | Any tool, app, or colleague can call your model |
| Share a `.pkl` file and hope they have the right Python version | One URL works from anywhere |
| Results are one-off | Results are on-demand, any time |
| Only you can use it | Clinicians, dashboards, EHRs can all integrate it |

> 💡 **For medical research specifically:** You can build a model once, then let a hospital dashboard, a mobile app, or a collaborator's R script all call the *same* model via its API — no Python needed on their end.

---

## The API Lifecycle (In 5 Steps)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   1. DESIGN      What does this API do? What inputs/outputs?│
│        ↓                                                    │
│   2. BUILD       Write the Python/FastAPI code              │
│        ↓                                                    │
│   3. TEST        Does it respond correctly?                 │
│        ↓                                                    │
│   4. DOCUMENT    Others need to know how to call it         │
│        ↓                                                    │
│   5. DEPLOY      Put it on a server so anyone can reach it  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

We will do **all 5 steps** in this tutorial.

---

## What Projects Are Good API Candidates?

Ask yourself: **"Would someone else want to call this automatically?"**

### ✅ Great for APIs:
- **NLP on clinical notes** — extract diagnoses, medications, SOAP summaries
- **Image classification** — pathology slides, X-ray triage
- **Risk scoring** — "give me a readmission risk score for this patient"
- **Drug interaction checker** — lookup + ML together
- **Literature search summarizer** — wrap PubMed + an LLM

### ❌ Less ideal for APIs (for now):
- One-off exploratory analysis (just use a notebook)
- Giant batch jobs that take hours (use a queue instead — though APIs *can* trigger these!)

---

## The Big Question: Does the Model Run Live or Pre-Computed?

This is the most important architecture decision:

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  OPTION A: Live Inference (model runs on each request)   │
│  ┌──────────┐   Request   ┌──────────┐   Result         │
│  │  Caller  │ ──────────► │  Model   │ ────────► JSON   │
│  └──────────┘             └──────────┘                  │
│  ✅ Always fresh   ❌ Slower, needs GPU/RAM              │
│                                                          │
│  OPTION B: Pre-computed (model ran offline, API looks up)│
│  ┌──────────┐   Request   ┌──────────┐   Result         │
│  │  Caller  │ ──────────► │  Cache / │ ────────► JSON   │
│  └──────────┘             │  DB      │                  │
│  ✅ Blazing fast  ❌ Can't handle new/unseen inputs      │
│                                                          │
│  OPTION C: Background Tasks (API accepts job, runs async)│
│  ┌──────────┐  Submit    ┌──────────┐                   │
│  │  Caller  │ ─────────► │  Queue   │ → Model runs...   │
│  └──────────┘            └──────────┘                   │
│       │   Later: "Is job 42 done?"      ↓               │
│       └──────────────────────────── Results ready ✅    │
│  ✅ Best of both  ⚠️  More complex to build             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**In this tutorial you will build all three.** By the end, you'll know exactly when to use each pattern.

---

## Key Terms Cheatsheet

| Term | Plain English |
|------|--------------|
| **Endpoint** | A specific URL that does one thing, e.g. `/classify` |
| **Request** | What you send to the API (the question) |
| **Response** | What comes back (the answer), usually JSON |
| **GET** | "Give me information" — used for lookups |
| **POST** | "Here's some data, process it" — used for predictions |
| **JSON** | The universal data format APIs use to talk |
| **OpenAPI/Swagger** | Auto-generated interactive docs for your API |
| **FastAPI** | The Python framework we'll use — it's fast, modern, and auto-documents |

---

## 📚 Reference Links

- [What is an API?](https://www.ibm.com/topics/api)
- [API Lifecycle explained](https://swagger.io/blog/api-development/stages-of-the-api-lifecycle/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)

---

➡️ **Ready? Move to [Step 1 →](../step_01_hello_api/README.md)**
