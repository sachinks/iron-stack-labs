# IS01P04 — Local LLM Gateway

> *"Data sovereignty begins at inference time. When sensitive data must not leave your infrastructure, the cloud API is not an option. Local inference is not a workaround — it is a first-class architectural choice with specific hardware requirements, performance tradeoffs, and security obligations."*

---

## What this project builds

A secure gateway that routes streaming chat requests to **any OpenAI-compatible backend** — Ollama, vLLM, or OpenAI cloud — by changing a single `.env` variable, with zero code changes between environments. The gateway is a FastAPI app with a `/health` check and a streaming `/chat` endpoint secured with **decentralized JWT token validation** utilizing a shared cryptographic secret. It is designed to sit in front of a locally bound Ollama instance so that the model is never directly reachable from the network — every request goes through one secure, authenticated choke point.

Stack: **FastAPI + AsyncOpenAI + sse-starlette + pydantic-settings + python-jose (JWT)**

---

## Why local inference

Four drivers push organisations toward local inference:

**Data privacy** — Healthcare records, legal contracts, and financial data cannot be sent to a third-party API under HIPAA, GDPR Article 28, and most enterprise data policies. Local inference is a compliance requirement, not a preference.

**Regulated industries** — Healthcare (HIPAA), legal (attorney-client privilege), finance (MiFID II, SOX). In each sector, "where does my data go?" has a regulatory answer. Local inference makes it: on your hardware.

**Cost at volume** — At low volume, cloud API cost is trivial. At ~10M tokens/day the economics invert. A single RTX 4090 serving a 7B model handles ~1,000 tokens/second — roughly $130/day of cloud cost avoided at small-model API pricing.

**Vendor lock-in avoidance** — Running entirely on one cloud API exposes you to pricing changes, deprecations, and outages outside your control. Ollama and vLLM both expose the OpenAI-compatible API — swap `base_url`, keep the code.

---

## Ollama vs vLLM vs llama.cpp

**llama.cpp** is the C++ inference engine underneath Ollama. Fast for a single user, runs on CPU or any GPU, but processes one request at a time — one user's KV cache occupies GPU memory for the full duration of their generation, and a second request waits. This is an architecture limitation, not a configuration issue.

**Ollama** wraps llama.cpp with a CLI, model download, and an OpenAI-compatible REST API on `localhost:11434`. Same serial limitation underneath; it saturates at ~3–5 concurrent users before latency degrades. The right choice for dev, single-user tools, and prototyping on any hardware.

**vLLM** is a high-throughput server built for multi-user production. Continuous batching and PagedAttention handle many concurrent users efficiently — roughly 35× the RPS of llama.cpp at peak load — but it needs a dedicated NVIDIA GPU. The same model runs on both; the same code calls both; you switch by changing `base_url`. That portability is exactly what this gateway exploits.

---

## PagedAttention

During autoregressive generation a transformer builds a **KV cache** — the Key and Value matrices from attention — for every token it has seen. The cache grows token by token and lives in GPU VRAM.

**The fragmentation problem.** Naive implementations pre-allocate the maximum possible KV cache when a request starts, because the final length is unknown. A request that generates 200 tokens still holds a reservation for 4,096 — wasting ~95% of the allocation. Under load, VRAM fills with reservations, not data, and the server serves far fewer users than the hardware should allow.

**What PagedAttention does.** It borrows OS virtual memory. The KV cache is split into fixed-size **pages** (~16 tokens each), allocated on demand as tokens are generated. Pages from different users interleave freely in VRAM — no pre-allocation, no fragmentation — and a **block table** (like an OS page table) maps logical token positions to physical pages. Result: 50%+ less memory waste, 2–4× throughput, ~35× RPS over llama.cpp at concurrent load.

---

## The endpoint swap

The entire backend choice lives in `.env`. Zero code changes between environments:

```bash
# Ollama (dev)
LLM_API_KEY=ollama
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=llama3.2:latest

# vLLM (production)
LLM_API_KEY=vllm-internal
LLM_BASE_URL=http://127.0.0.1:8001/v1
LLM_MODEL=meta-llama/Llama-3.3-70B-Instruct

# OpenAI cloud
LLM_API_KEY=sk-...
LLM_BASE_URL=
LLM_MODEL=gpt-4o-mini
```

`gateway/llm_client.py` passes `base_url=settings.llm_base_url or None` — an empty `LLM_BASE_URL` falls back to the OpenAI SDK default (the real OpenAI cloud), so the same code reaches all three backends. This portability is architectural, not accidental: both Ollama and vLLM expose the OpenAI-compatible API deliberately, so any code written against the OpenAI SDK works unchanged.

---

## Security architecture

In May 2026, internet-wide scans found ~175,000 Ollama instances exposed on public IPs. Ollama has **zero built-in authentication**. This project protects inference at both the network and gateway layers:

1. **Ollama is bound to `127.0.0.1` only** via a systemd override:
   ```
   [Service]
   Environment="OLLAMA_HOST=127.0.0.1:11434"
   ```
   Verify: `curl http://{lan_ip}:11434/api/tags` → `connection refused`. The model is invisible to the network; only processes on the host can reach it.

2. **Decentralized Authorization:** Every query targeting `/chat` requires a valid JWT access token issued by the Multitenant API (`is01p03`) using a shared `secret_key`. This secures Ollama by acting as an authenticated gateway.

---

## How to install & run

```bash
# 1. Create and activate the virtual environment outside the workspace
python3 -m venv ~/venvs/islab/is01p04 && source ~/venvs/islab/is01p04/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure local environment variables
cat > .env <<'ENV'
LLM_API_KEY=ollama
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=llama3.2:latest
SECRET_KEY=yoursecretkeyhere
LOG_LEVEL=INFO
ENV

# 4. Start Ollama and run the gateway
ollama serve && ollama pull llama3.2
uvicorn main:app --reload

# 5. Stream a completion with an Authorization header
curl -N -X POST http://127.0.0.1:8000/chat \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <JWT_TOKEN>" \
     -d '{"prompt":"Explain SSE in one sentence."}'
```

---

## Project structure

```
is01p04-local-llm-gateway/
  main.py                 FastAPI app: GET /health, POST /chat (secured token streaming)
  config.py               pydantic-settings: configuration settings with safe fallbacks
  logger.py               rotating file logging and stdout console tracing
  auth/
    __init__.py           package initialization
    jwt_utils.py          stateless token verify mechanism
    dependencies.py       get_current_user HTTPBearer dependency
  gateway/
    __init__.py           package initialization
    llm_client.py         get_llm_client() wrapper building AsyncOpenAI client
  requirements.txt        project dependencies list
  README.md               this document
```

---

## Algorithm & code flow

### `config.py` — settings
`Settings(BaseSettings)` declares required keys with default fallbacks and exception handling inside a wrapper instantiation block, ensuring compile-time safety.

### `gateway/llm_client.py` — the client builder
`get_llm_client()` instantiates `AsyncOpenAI` using settings. Any exception is caught and logged.

### `auth/jwt_utils.py` — stateless verify
`verify_token(token)` calls `jwt.decode` using the shared secret and HS256 algorithm. Converts library exceptions into domain exceptions.

### `main.py` — endpoints
- **`GET /health`** → `{"status": "ok"}`.
- **`POST /chat`** Secured by `Depends(get_current_user)`. Reads prompt, connects to `get_llm_client()`, and yields tokens asynchronously using `EventSourceResponse`. Yields `[DONE]` upon completion or `[ERROR] ...` on exception.

---

## Observed

- **One codebase, three backends.** Swapping `LLM_BASE_URL` allows streaming from Ollama, vLLM, or OpenAI with zero code change.
- **Ollama is unreachable off-host.** Direct network connections to Ollama return `connection refused`.
- **JWT authorization is enforced.** Calling `/chat` without a valid bearer token fails immediately with `401 Unauthorized`.

---

## BENEATH

**What PagedAttention pages, where it pages to, and why a naive KV cache fragments.**

Every token a transformer generates requires the Key and Value matrices of all previous tokens — the KV cache — whose size grows linearly with sequence length. A naive implementation pre-allocate the maximum possible length (e.g. 4,096 tokens) per request at start time, because the final length is unknown. A request that ends at 200 tokens held a full 4,096-token reservation throughout — roughly 1.9GB reserved, ~180MB used. Under concurrent load, VRAM fills with these over-reservations, and a server that should support 30+ users serves 3.

PagedAttention pages the **KV cache** — specifically the Key and Value tensors accumulated during attention. These are divided into fixed-size **pages** (~16 tokens). Pages live in GPU VRAM, with CPU RAM as a swap destination under pressure. A **block table** — directly analogous to an OS page table — maps each request's logical token positions to physical page addresses, and attention is modified to work with those non-contiguous addresses. Pages are allocated one at a time, on demand, as tokens are generated, and pages from multiple requests interleave freely in VRAM. That tight packing is why the technique is named after OS paging.

**Why llama.cpp fails at multi-user concurrency:** it allocates one full KV cache block per request and holds it for the entire generation — no batching, no sharing. A second request cannot start until the first frees its cache. At 5+ concurrent users, requests queue serially and latency grows linearly. vLLM's continuous batching processes tokens from many requests in the same step, which is why the peak-load RPS gap is ~35× — architectural, not a tuning parameter.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
