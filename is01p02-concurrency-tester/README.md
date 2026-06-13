# IS01P02 — Concurrency Tester

**Layer 01 · Information Flow Architecture · Chapter 02**

> *"Blocking on an LLM call is not a performance problem — it is an architectural failure. One synchronous call freezes the entire event loop, and every other user queues behind it."*

---

## What this project builds

A measurement harness that proves, with real latency numbers from a running FastAPI server, the difference between three request-handling patterns: a **sync** handler (`requests`, blocks the loop), an **async** handler (`httpx.AsyncClient`, yields to the loop), and a **fake** handler (`asyncio.sleep`, isolates the event-loop effect from LLM variance). Two standalone demos (`sleep_demo.py`, `gather_demo.py`) reduce the same lesson to its smallest form, and a benchmark script drives the server and prints P50/P95/wall-time tables.

When a server handles LLM calls synchronously, every user waits behind every other user. One 4-second LLM call means the second user waits 4 seconds before their request even starts; twenty users means the last waits 80 seconds. This project measures that gap instead of asserting it, and provides a plotting script using Matplotlib to visualize the latency distributions.

---

## How the asyncio event loop works

The event loop is a single-threaded scheduler that runs in a continuous loop. On each tick it does three things: it runs all callbacks currently in the ready queue, then calls the OS selector (`epoll` on Linux) to ask which file descriptors are ready for I/O, then moves any coroutines waiting on those descriptors back into the ready queue.

When your coroutine hits an `await`, Python suspends it at that exact line — saving the stack frame, local variables, and execution position — and hands the file descriptor to the OS selector. The loop is now free to run other coroutines. When the OS signals that the response is ready, the loop resumes the suspended coroutine from exactly where it paused.

The CPU is never idle during an `await`. It is polling the OS for I/O readiness on all registered sockets simultaneously. One thread. No parallelism. Cooperative concurrency only.

---

## The two async killers

**Killer 1 — Synchronous library inside an async handler**

Using a synchronous library like `requests` or `time.sleep` inside an async handler blocks the entire Python thread for the full duration of the call. No `await` is hit, so the event loop never gets control back. Every other coroutine queues behind it — turning a concurrent server back into a serial one.

```python
# WRONG — blocks the event loop
async def bad_handler(prompt: str):
    import requests
    response = requests.post(LLM_URL, json={...})  # blocks 4s, loop frozen

# CORRECT — yields to the event loop
async def good_handler(prompt: str):
    response = await httpx_client.post(LLM_URL, json={...})  # loop is free
```

Common traps: `requests` → `httpx.AsyncClient`; `time.sleep()` → `await asyncio.sleep()`; `psycopg2` → `asyncpg`.

**Killer 2 — CPU-bound work inside an async handler**

Even with fully async code, CPU-intensive work blocks the loop because the thread is executing Python bytecode continuously — no `await` is ever hit. Examples: PDF parsing, numpy operations, local model inference. The fix is `ProcessPoolExecutor` — separate processes, each with their own interpreter and GIL. That is true parallelism.

```python
from concurrent.futures import ProcessPoolExecutor
_pool = ProcessPoolExecutor()

async def good_handler(path: str):
    loop = asyncio.get_event_loop()
    pages = await loop.run_in_executor(_pool, parse_pdf_sync, path)
```

---

## GIL and asyncio

Asyncio does not bypass the GIL — it does not need to. Asyncio runs entirely within a single thread, so there is never any competition for the GIL. For I/O-bound work the GIL is irrelevant because the bottleneck is the network: when a coroutine hits `await`, the OS selector call (`epoll_wait`) is a C-level syscall that releases the GIL while waiting. For CPU-bound work the GIL is a real bottleneck — `ThreadPoolExecutor` cannot parallelise Python bytecode, so `ProcessPoolExecutor` (separate GILs) is the correct tool.

---

## How to install & run

```bash
# 1. Activate the native WSL virtual environment
source ~/venvs/islab/is01p02/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Ollama (separate terminal) — only needed for the OLLAMA benchmarks
ollama serve && ollama pull llama3.2

# 4a. Standalone demos (no server needed)
python sleep_demo.py     # asyncio.sleep vs time.sleep, 10 concurrent
python gather_demo.py    # sequential vs asyncio.gather over 5 LLM calls

# 4b. Server + benchmark
uvicorn main:app --reload                 # terminal A
python -m benchmark.run_benchmark         # terminal B
python -m benchmark.plot_results          # terminal B (generates graph)
```

Config (`config.py`, overridable via `.env`): `MODEL_NAME` (`llama3.2`), `OPENAI_BASE_URL` (`http://localhost:11434/v1`), `CONCURRENT_USERS` (`10`), `REQUESTS_PER_USER` (`5`), `TEST_PROMPT`.

---

## Project structure

```
is01p02-concurrency-tester/
  main.py                     FastAPI app: lifespan-managed shared httpx client + 3 routers
  config.py                   pydantic-settings: model, base_url, load parameters
  logger.py                   Custom level-based logger with console and rotating file outputs
  handlers/
    sync_handler.py           POST /sync/chat   — requests (blocking)
    async_handler.py          POST /async/chat  — shared httpx.AsyncClient (non-blocking)
    fake_handler.py           GET  /fake        — asyncio.sleep(2), isolates loop effect
  benchmark/
    run_benchmark.py          drives the endpoints, prints P50/P95/wall-time tables
    plot_results.py           drives endpoints and plots P50/P95 bar chart comparison
  sleep_demo.py               asyncio.sleep vs time.sleep, 10 concurrent
  gather_demo.py              sequential vs asyncio.gather, 5 LLM calls
  requirements.txt            Project dependencies
  .env.example                Template for environment variables
  .gitignore                 Git ignored files and cache dirs
  README.md                   This document
```

---

## Algorithm & code flow

### `main.py` — the shared async client
A `lifespan` async context manager creates one `httpx.AsyncClient(timeout=120.0)` at startup, stores it on `app.state.client`, and `aclose()`s it on shutdown. Three routers are mounted: sync, async, fake. The single shared client is the point — a fresh client per request would defeat connection pooling.

### `handlers/sync_handler.py` — the blocking baseline
`POST /sync/chat` is a plain `def` (not `async`) that calls `requests.post(..., timeout=60)`. Under uvicorn this runs in a threadpool, but it models the "blocking library" failure: it returns `{response, latency_ms, handler: "sync"}`.

### `handlers/async_handler.py` — the correct pattern
`POST /async/chat` is `async def`, pulls the shared client off `request.app.state.client`, `await`s the POST, calls `response.raise_for_status()`, and returns `{response, latency_ms, handler: "async"}`. The `await` is where the loop is freed to serve other requests.

### `handlers/fake_handler.py` — the clean experiment
`GET /fake` is `async def fake()` that just `await asyncio.sleep(2)`. No LLM, no network variance — so a sequential-vs-concurrent comparison here measures *only* the event loop's ability to overlap waits.

### `benchmark/run_benchmark.py` — the harness
`fetch()` times a single request with `time.time()`. `run_benchmark(url, label, concurrent, method, params)` fires `CONCURRENT_USERS` requests either via `asyncio.gather` (concurrent) or a `for` loop (sequential), inside one `httpx.AsyncClient(timeout=300.0)`. It reports `p50 = statistics.median(times)`, `p95 = statistics.quantiles(times, n=20)[18]`, plus summed and wall-clock time.

---

## Observed

### Benchmark — server, 10 concurrent requests (WSL Ubuntu, local Ollama `llama3.2`)

| | Wall Time | P50 | P95 |
|---|---|---|---|
| SYNC FAKE (sequential) | 20.083s | 2.005s | 2.043s |
| ASYNC FAKE (concurrent) | **1.996s** | 1.992s | 1.995s |
| SYNC OLLAMA | 29.498s | 18.690s | 30.656s |
| ASYNC OLLAMA | 25.979s | 14.680s | 27.244s |

ASYNC FAKE is **10× faster** wall time than SYNC FAKE — all 10 requests sleep simultaneously. Ollama shows smaller gains because it is single-threaded and queues requests internally regardless of how concurrently they arrive.

### `gather_demo.py` — 5 LLM calls

```
Sequential 5 calls: 6614ms
Parallel   5 calls: 2157ms
Speedup:            3.1x
```

Why not 5×? Ollama processes one request at a time internally. Parallel calls save network and queuing overhead but not inference time. Against a cloud provider that batches parallel inference, the speedup would approach 4.5–5×.

### `sleep_demo.py` — 10 concurrent, 1s each

```
10x asyncio.sleep(1): 1002ms   — all 10 ran simultaneously
10x time.sleep(1):   10005ms   — ran one by one, loop was blocked
Ratio: 10.0x slower with time.sleep
```

---

## BENEATH

**What is the event loop doing while an `await` is suspended — is the CPU idle?**

No. When a coroutine hits `await`, the loop suspends it and registers its file descriptor with the OS selector (`epoll_wait` on Linux, a C-level syscall). While waiting for I/O it runs other coroutines from the ready queue. The CPU is actively polling for socket readiness and processing other requests. Nothing is idle.

**I/O-bound vs CPU-bound — the fundamental difference**

I/O-bound work spends most of its time waiting for external responses — network, disk, database. Asyncio converts that OS-level block into an event-loop wait, freeing the thread to handle other coroutines. Our benchmark proves it: ASYNC FAKE wall time 1.996s vs SYNC FAKE 20.083s for 10 concurrent requests. CPU-bound work executes Python bytecode continuously — no `await` is ever hit, the loop never regains control, and asyncio provides zero benefit. `ProcessPoolExecutor` is required there.

**Does asyncio bypass the GIL?**

No. Asyncio is single-threaded — one thread, one GIL, no competition, so the GIL is simply not relevant. What makes async I/O fast is not bypassing the GIL but cooperative suspension at `await` points, which lets one thread handle many concurrent I/O waits. The sleep demo confirms it: 10 concurrent `asyncio.sleep(1)` finished in 1002ms; 10 concurrent `time.sleep(1)` took 10005ms.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
