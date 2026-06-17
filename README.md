# Iron Stack Labs

> *"The engineer who ships, measures, and fixes beats the engineer who only reads."*

A progressive systems engineering project workspace demonstrating the incremental design and implementation of real-world backend systems using Python and FastAPI. Each project is built step by step, with every checkpoint committed to its own Git branch and tagged for easy reference.

---

## Projects

| Project | System | Core Technologies |
| :--- | :--- | :--- |
| **IS01P01** | [LiveChat Support API](./is01p01-livechat-api/) | FastAPI · OpenAI Streaming · Server-Sent Events |
| **IS01P02** | [Concurrency Tester](./is01p02-concurrency-tester/) | FastAPI · Sync/Async Benchmarking · Matplotlib |
| **IS01P03** | [Multitenant API](./is01p03-multitenant-api/) | FastAPI · JWT Auth · Redis Rate Limiting · LIFO Middleware |
| **IS01P04** | [Local LLM Gateway](./is01p04-local-llm-gateway/) | FastAPI · Swappable LLM Client · Stateless JWT · Streaming |

---

## Branch Structure

Each project is built incrementally. Every step in the build has its own dedicated branch and Git tag, allowing you to checkout any specific stage of the implementation.

```
main  (latest complete state)
 │
 ├── IS01P01: LiveChat Support API
 │    ├── l1-is01p01-step-1   (v1.1.0-step1)  Baseline scaffold & logging
 │    ├── l1-is01p01-step-2   (v1.1.0-step2)  Request model & validation
 │    ├── l1-is01p01-step-3   (v1.1.0-step3)  Async OpenAI token streaming
 │    ├── l1-is01p01-step-4   (v1.1.0-step4)  Static HTML SSE client UI
 │    └── l1-is01p01-step-5   (v1.1.0-final)  README & final polish
 │
 ├── IS01P02: Concurrency Tester
 │    ├── l1-is01p02-step-1   (v1.2.0-step1)  Baseline & fake async route
 │    ├── l1-is01p02-step-2   (v1.2.0-step2)  Sync vs async sleep demo
 │    ├── l1-is01p02-step-3   (v1.2.0-step3)  Modular routing & lifespan
 │    ├── l1-is01p02-step-4   (v1.2.0-step4)  Benchmark harness & plotting
 │    └── l1-is01p02-step-5   (v1.2.0-final)  README & final polish
 │
 ├── IS01P03: Multitenant API
 │    ├── l1-is01p03-step-1   (v1.3.0-step1)  Scaffold & health check
 │    ├── l1-is01p03-step-2   (v1.3.0-step2)  Models & Redis client
 │    ├── l1-is01p03-step-3   (v1.3.0-step3)  JWT utils & auth router
 │    ├── l1-is01p03-step-4   (v1.3.0-step4)  Auth, rate limit & logging middleware
 │    ├── l1-is01p03-step-5   (v1.3.0-step5)  LIFO middleware stack & endpoints
 │    └── l1-is01p03-step-6   (v1.3.0-final)  README & final polish
 │
 └── IS01P04: Local LLM Gateway
      ├── l1-is01p04-step-1   (v1.4.0-step1)  Baseline config & health route
      ├── l1-is01p04-step-2   (v1.4.0-step2)  LLM client adapter & mock endpoint
      ├── l1-is01p04-step-3   (v1.4.0-step3)  Stateless JWT auth package
      ├── l1-is01p04-step-4   (v1.4.0-step4)  Streaming completions via SSE
      └── l1-is01p04-step-5   (v1.4.0-final)  README & final polish
```

### Checking Out a Specific Step

```bash
# By branch
git checkout l1-is01p03-step-4

# By tag
git checkout v1.3.0-step4
```

---

## Getting Started

Each project has its own `README.md`, `requirements.txt`, and `.env.example`. Navigate into the project directory and follow its setup instructions.

```bash
# Example: IS01P01
cd is01p01-livechat-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload
```

---

## Design Principles

All projects share three core engineering standards:

1. **Structured Exception Safety** — every endpoint and service boundary is wrapped in try/except blocks, capturing trace context and surfacing clean HTTP errors.
2. **Rotating Level-Based Logging** — each project ships a size-capped `RotatingFileHandler` writing to `logs/app.log`, alongside a stdout `StreamHandler` for container-friendly output.
3. **Twelve-Factor Configuration** — all runtime secrets and environment-specific settings are loaded from `.env` via `pydantic-settings`, keeping configuration cleanly separate from code.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
