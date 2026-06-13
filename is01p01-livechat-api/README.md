# IS01P01 — LiveChat Support API

> *"Every API is a transformation pipeline. Data enters as a user prompt, changes shape at each layer, and exits as streaming tokens rendered in the browser. Get the order of those transformations wrong — validate after the stream opens, compress the stream, buffer it behind a proxy — and the pipeline silently breaks while still returning 200 OK."*

---

## What this project builds

A **streaming chat API** — the same pattern powering ChatGPT, Claude, and every AI product that shows words appearing one by one. The server pushes tokens to the browser as they arrive using **Server-Sent Events (SSE)** semantics, instead of waiting for the full response.

A single async generator (`stream_tokens`) bridges a local LLM (Ollama, via the OpenAI-compatible API) to the browser. Pydantic validates the request *before* the stream opens. `sse-starlette` wraps the generator into a long-lived HTTP response. A modern glassmorphic static page consumes the stream and paints tokens to the DOM as they land.

Stack: **FastAPI + uvicorn + Ollama + AsyncOpenAI + sse-starlette + Pydantic v2**

---

## Architecture — the data transformation pipeline

```
Browser  (static/index.html)
  │  1. User types a message, clicks Send
  │  2. fetch POST /chat  with JSON body { "message": "..." }
  ↓
ASGI server (uvicorn)
  │  3. Accepts the connection, hands it to the FastAPI app
  ↓
FastAPI endpoint  (main.chat)
  │  4. Pydantic validates ChatRequest BEFORE the stream opens
  │     A 422 here is a clean HTTP error — see "validation timing" below
  ↓
Async generator  (streaming.stream_tokens)
  │  5. Builds an AsyncOpenAI client pointed at Ollama's /v1
  │  6. Opens a streaming chat completion against the local model
  │  7. For each chunk, extracts delta.content and yields { "data": token }
  │  8. On completion yields { "data": "[DONE]" }; on error { "data": "[ERROR] ..." }
  ↓
sse-starlette  (EventSourceResponse)
  │  9. Serialises each yielded dict into SSE wire format: "data: <token>\n\n"
  │ 10. Keeps the TCP connection open while the generator is still yielding
  ↓
Browser  (fetch ReadableStream reader)
  │ 11. response.body.getReader() reads raw bytes as they arrive
  │ 12. TextDecoder turns bytes into text; lines split on "\n"
  │ 13. Lines starting with "data: " are unwrapped; [DONE] ends the read
  ↓
User sees words appear on screen, one token at a time
```

---

## Key dependencies

| Package | Why it exists |
|---|---|
| `fastapi` | Web framework — routing, request models, OpenAPI docs |
| `uvicorn` | ASGI server — runs FastAPI, handles the async connection |
| `pydantic-settings` | Manages environment variables and configuration parameters |
| `openai` (AsyncOpenAI) | Client that talks to Ollama through the OpenAI-compatible `/v1` API |
| `sse-starlette` | Turns an async generator into a valid SSE HTTP response |
| `httpx` | Async HTTP transport used under the OpenAI SDK |
| `aiofiles` | Async file serving support |

---

## The validation timing rule

**Validate before the stream opens. Never after.**

Once `EventSourceResponse` starts, the HTTP status is already `200 OK` — it is committed to the wire. Any error raised inside the generator *cannot* change that status code; the browser already accepted the connection as successful. So all rejectable conditions must be checked in the endpoint, before the response object is returned.

```python
# CORRECT — validate first, then open the stream
@app.post("/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    return EventSourceResponse(stream_tokens(request.message))

# WRONG — an error inside the stream is invisible to the HTTP status
async def stream_tokens(message):
    if not message:        # too late — 200 already sent
        yield {"data": "error"}
```

In this project there are *two* layers of validation, and the order matters. Pydantic's `min_length=1` on the model rejects an empty/missing `message` field with a `422` automatically. The explicit `request.message.strip()` check then catches whitespace-only messages (`"   "`) that pass `min_length` but are still empty in spirit — again returning `422` before the stream opens.

---

## Production traps

### GZip middleware trap
If `GZipMiddleware` is added to the app, it tries to compress the SSE response. Compression buffers chunks to build a compressible block — destroying the real-time effect. Tokens arrive in batches instead of one by one. **Fix:** exclude `/chat` from GZip.

### Nginx reverse-proxy trap
Nginx buffers upstream responses by default. An SSE stream behind Nginx appears frozen — tokens accumulate in Nginx's buffer and flush all at once. **Fix:** in the location block, `proxy_buffering off;` and emit the `X-Accel-Buffering: no` response header.

---

## SSE wire format — what actually travels over the network

SSE has no `more_data` flag. The protocol uses two implicit signals:
- **Connection stays open** = generator is still yielding, more tokens coming.
- **Connection closes** = generator exhausted, streaming done.

Each event on the wire looks like this:

```
data: Hello\n\n
data:  world\n\n
data: !\n\n
data: [DONE]\n\n
```

Rules: every event starts with `data: `; every event ends with `\n\n`; `[DONE]` is a custom end-of-stream convention, **not** part of the SSE spec.

### A note on the client in this project

The browser code in `static/index.html` does **not** use the `EventSource` API. It uses `fetch()` plus a manual `ReadableStream` reader:

```javascript
const reader = response.body.getReader();
const decoder = new TextDecoder();
function read() {
  reader.read().then(({ done, value }) => {
    if (done) return;
    decoder.decode(value).split('\n').forEach(line => {
      if (line.startsWith('data: ')) {
        const token = line.slice(6);
        if (token === '[DONE]') return;
        out.textContent += token;
      }
    });
    read();
  });
}
```

Why `fetch` instead of `EventSource`? `EventSource` only issues `GET` requests and cannot send a JSON body — this endpoint is a `POST` with a JSON payload, so the manual reader is required. The trade-off: the client must split lines and strip the `data: ` prefix by hand, which `EventSource` would otherwise do for free. This is the single most common real-world reason to hand-roll SSE consumption.

---

## How to install & run

```bash
# 1. Activate the native WSL virtual environment
source ~/venvs/islab/is01p01/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Ollama in a separate terminal and pull the model
ollama serve
ollama pull llama3.2

# 4. Create local environment configuration if needed
cp .env.example .env

# 5. Run the API
uvicorn main:app --reload

# 6. Open the UI in browser
#    http://127.0.0.1:8000
```

---

## Project structure

```
is01p01-livechat-api/
  main.py            FastAPI app: POST /chat, GET / (serves the UI)
  streaming.py       stream_tokens() async generator → AsyncOpenAI → Ollama
  models.py          ChatRequest pydantic model (min_length=1, max_length=4096)
  config.py          Pydantic BaseSettings class loading configuration
  logger.py          Custom level-based logger with console and rotating file outputs
  static/index.html  Elegant glassmorphic fetch + ReadableStream client
  requirements.txt   Project dependencies
  .env.example       Template for local variables configuration
  .gitignore         Git ignored directories (cache, logs, secrets)
  README.md          This document
```

---

## Algorithm & code flow

### `config.py` — environment settings
Instantiates the `Settings` class inheriting from `BaseSettings`. Loads variables from environmental fields or `.env`, validating variables before loading. Includes safe `try-except` fallback initialization.

### `logger.py` — tracing logger
Initializes the stdout StreamHandler alongside a size-capped `RotatingFileHandler` writing logs to `logs/app.log` (5 MB, max 5 backups). Creates target folders dynamically and logs standard lifecycle events with try-except safety.

### `models.py` — request contract
`ChatRequest` has one field: `message: str = Field(..., min_length=1, max_length=4096)`. `...` makes it required; `min_length=1` rejects empty strings; `max_length=4096` caps prompt size at the API boundary so an oversized body never reaches the model.

### `main.py` — routing and validation
`app = FastAPI(title="Iron Stack — LiveChat API")` and `app.mount("/static", StaticFiles(...))`.

- **`POST /chat`** (`async def chat`) — receives a validated `ChatRequest`. Guards `if not request.message.strip()` → `HTTPException(422)`. Returns `EventSourceResponse(stream_tokens(request.message))`. Validation runs *before* the response object is constructed, so a rejection is a real `422`.
- **`GET /`** (`async def home`) — returns `FileResponse("static/index.html")`, the chat UI.

### `streaming.py` — the token generator
`async def stream_tokens(message)`:
1. Builds `AsyncOpenAI(base_url=f"{settings.OLLAMA_BASE_URL}/v1", api_key="ollama")` — Ollama ignores the key but the SDK requires a non-empty one.
2. `await client.chat.completions.create(model=settings.OLLAMA_MODEL, messages=[{"role": "user", "content": message}], max_tokens=settings.MAX_TOKENS, stream=True)`.
3. `async for chunk in stream`: reads `token = chunk.choices[0].delta.content`; yields `{"data": token}` only when `token` is truthy (the final chunk carries `None`).
4. After the loop, yields `{"data": "[DONE]"}`.
5. `except Exception as e`: yields `{"data": f"[ERROR] {e}"}` — surfaced to the user instead of a dropped connection.
6. `finally: await client.close()` — releases the HTTP connection on every path, including error and client-disconnect.

---

## Observed

- **Streaming is visible end-to-end.** With `llama3.2` on a local Ollama, tokens paint to the page incrementally rather than appearing all at once — the SSE path works.
- **Whitespace-only messages return a clean 422.** `"   "` passes Pydantic's `min_length=1` (it is length 3) but is caught by the `.strip()` guard, so the failure is an HTTP error, not a silent empty stream. This is exactly the validation-timing rule paying off.
- **Errors arrive in-band.** When Ollama is not running, the generator's `except` yields `[ERROR] ...` and the page shows it — the connection does not just hang, because the `200` was already committed and the error had to travel as stream content.
- **`EventSource` was a dead end.** The first instinct (use the browser's native `EventSource`) fails immediately because the endpoint is a `POST` with a JSON body; `EventSource` only does `GET`. The `fetch` + reader approach is the consequence, not a stylistic choice.

---

## BENEATH — what actually happens when a single token arrives

1. Ollama generates one token and writes it to its output buffer.
2. The `AsyncOpenAI` client receives the chunk over async HTTP streaming and yields a chunk object.
3. `stream_tokens` extracts `chunk.choices[0].delta.content` — a short string fragment.
4. The generator yields `{"data": token}`.
5. `EventSourceResponse` serialises that to the bytes `data: <token>\n\n` and flushes them to the ASGI layer immediately.
6. uvicorn writes those bytes to the open TCP socket — nothing signals "more coming"; silence on an open connection *is* the signal.
7. In the browser, `reader.read()` resolves with the new bytes; `TextDecoder` decodes them; the line is split, the `data: ` prefix stripped, and the token appended to the DOM.
8. The reader loop calls itself again and parks on the next `read()` until more bytes arrive — until a `data: [DONE]` line ends it.

The whole effect of "words appearing one at a time" is just this loop running fast enough that each token's round trip is shorter than human perception.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
