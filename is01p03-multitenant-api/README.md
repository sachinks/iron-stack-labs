# IS01P03 — Multitenant API

> *"A demo API and a production API have completely different failure modes. A demo fails when the logic is wrong. A production API fails when authentication is bypassed, a free-tier user drains quota that belongs to paying customers, or a 3am incident cannot be diagnosed because there are no structured logs. Middleware and dependencies are the gap."*

---

## What this project builds

A FastAPI service with the three things that separate a production API from a demo: **JWT-based authentication**, **Redis-backed per-tenant rate limiting** across three pricing tiers, and **two layers of request logging** — one GDPR-safe (redacts credentials), one structured (request id, hashed IP, latency). Auth, logging, and rate limiting run as ASGI middlewares so every route is covered automatically in a unified LIFO pipeline. A simulated per-tenant data store demonstrates **tenant isolation**: a caller can only read their own records.

Stack: **FastAPI + python-jose (JWT) + redis.asyncio + pydantic-settings + Starlette middleware**

---

## JWT structure and verification

A JWT has three dot-separated parts: **header**, **payload**, **signature**. The header names the algorithm (`HS256`). The payload carries the claims — here `sub` (user id), `tier` (`free`/`pro`/`enterprise`), and `exp` (expiry). The signature is an HMAC-SHA256 of `base64(header).base64(payload)` using the server's secret key.

On receipt, the server recomputes the signature from the header and payload it received and compares it to the token's signature. If they match and `exp` is in the future, the token is valid — **no database lookup required**. The server trusts the payload because only it holds the secret key.

A JWT without an `exp` claim is a permanent credential. This project sets `exp = now + 60 minutes` on every token (`auth/jwt_utils.py`).

---

## Middlewares Stack and Registration Order

All request gating, rate limiting, and logging run as ASGI middlewares configured in a LIFO stack in `main.py`:

```
Incoming request
  → GDPRLoggerMiddleware      (outermost: intercepts first, strips credentials from output)
    → RequestLoggerMiddleware (logs request/response metrics, hashed client IP, req_id)
      → AuthMiddleware        (verifies JWT token, populates request.state.user context)
        → RateLimitMiddleware (performs atomic Redis INCR to rate limit based on tier)
          → Route handler     (executes endpoints like /me or /data/{user_id})
```

`add_middleware` in Starlette is LIFO: the **last** registered is outermost. `main.py` registers the middlewares in the following order:
1. `RateLimitMiddleware`
2. `AuthMiddleware`
3. `RequestLoggerMiddleware`
4. `GDPRLoggerMiddleware`

Because of LIFO wrapping, `GDPRLoggerMiddleware` is the outermost boundary. The security consequence of order is critical: `AuthMiddleware` must run *before* `RateLimitMiddleware` on the request pathway, because rate limiting is tenant-aware and requires `request.state.user` context. If rate limiting ran before authentication, an unauthenticated caller could exhaust rate limit quotas anonymously.

---

## Redis rate limiting — three tiers

An in-memory counter fails with multiple workers: each worker process has its own memory, so a counter in worker 1 is invisible to worker 2. Under load balancing, requests spread across workers and each sees a fraction of the true count.

Redis `INCR` is atomic at the protocol level. Redis executes commands single-threaded, so `INCR key` — read, increment, write — completes without interruption. No race condition is possible even under thousands of concurrent requests from multiple workers.

The key is `rate_limit:{user_id}:{YYYY-MM-DDTHH:MM}` — a **fixed one-minute window**. On the first request each minute, `INCR` returns `1` and a 60-second TTL is set; subsequent requests increment. When the count exceeds the tier limit, a `429` is returned. The tier limits (`config.py` → `TIER_LIMITS`):

| Tier | Requests / minute |
|---|---|
| `free` | 10 |
| `pro` | 60 |
| `enterprise` | 300 |

---

## Two layers of request logging

This project runs **two** logging middlewares, each answering a different question.

**`RequestLoggerMiddleware` (operational).** Generates an 8-char `req_id`, stores it on `request.state`, hashes the client IP to `sha256(ip)[:8]`, times the request with `perf_counter`, and logs one line: method, path, status, duration in ms, `req_id`, IP hash, response size. This is the line you grep at 3am.

```
POST /me → 200 in 12.4ms | req_id=a1b2c3d4 | ip=9f8e7d6c | resp=41b
```

**`GDPRLoggerMiddleware` (compliance).** Reads the `Authorization` header and, if it starts with `bearer `, replaces the value with `Bearer [REDACTED]` *before* logging — so the raw JWT never lands in a log file. Logs method, path, redacted auth, and status with a timestamped formatter.

The redaction operates only on the log string; the original request object is untouched, so downstream handlers still see the real token.

---

## GDPR compliance

Two things are never logged raw: the JWT and the user id. The JWT is a credential; logging it creates a permanent record of it. The user id is PII. `RequestLoggerMiddleware` already logs the IP as `sha256(ip)[:8]` rather than the raw address — enough to correlate a session for debugging without storing the identifier. When a user exercises their right to erasure, you delete hashed references rather than raw PII, because the raw PII was never written.

---

## How to install & run

```bash
# 1. Create and activate the virtual environment outside the workspace
python3 -m venv ~/venvs/islab/is01p03 && source ~/venvs/islab/is01p03/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Redis (rate limiting depends on it)
redis-server                      # or: docker run -p 6379:6379 redis

# 4. Provide a secret key and run
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
uvicorn main:app --reload
```

---

## Project structure

```
is01p03-multitenant-api/
  main.py                     app + LIFO middleware wiring + /health, /me, /data endpoints
  config.py                   pydantic-settings + TIER_LIMITS dict
  redis_client.py             connection pool lifecycle + async Redis client
  models.py                   in-memory tenant isolated store (TENANT_DATA)
  auth/
    __init__.py               package initialization
    jwt_utils.py              create_access_token / verify_token (HS256)
    dependencies.py           get_current_user dependency helper
    routes.py                 auth router with login endpoint
  middleware/
    __init__.py               package initialization
    auth.py                   AuthMiddleware — extracts JWT and populates request state
    rate_limit.py             RateLimitMiddleware — Redis fixed-window limit check
    logging.py                RequestLoggerMiddleware — req_id, IP hash, latency logging
    gdpr_logger.py            GDPRLoggerMiddleware — redacts Authorization header in logs
  requirements.txt            project dependencies
  README.md                   this document
```

---

## Algorithm & code flow

### `config.py` — settings + tier table
`Settings(BaseSettings)` reads from `.env`. If `.env` is missing, it falls back gracefully to default settings with warnings. `TIER_LIMITS` maps tier names to limits.

### `auth/jwt_utils.py` — issue & verify
- `create_access_token(user_id, tier)` builds token payload and encodes it with `HS256`.
- `verify_token(token)` decodes the JWT and raises a `ValueError` if the signature is invalid or expired.

### `middleware/auth.py` — token extractor
Intercepts non-public routes, extracts token from `Authorization: Bearer <token>`, verifies it, and sets `request.state.user`. Returns a `401 Unauthorized` response immediately on failure.

### `middleware/rate_limit.py` — the quota check
Applies to authenticated requests. Performs atomic `INCR` in Redis on a one-minute window key. Returns a `429 Too Many Requests` response on limit excess.

### `middleware/logging.py` & `middleware/gdpr_logger.py`
Loggers subclassing `BaseHTTPMiddleware` to trace performance latency and log GDPR-compliant redacted details to rotating files and console.

---

## Observed

- **Tenant isolation holds.** A token for `sachin` reads `/data/sachin` (200) but is refused `/data/bob` with `403 Forbidden`.
- **Rate limiting trips at the tier boundary.** A `free` token returns `429` on the 11th request inside the same minute.
- **Credentials never reach the logs.** Hashed IPs and redacted `Bearer [REDACTED]` logs are recorded.

---

## BENEATH

**What is ASGI middleware at the protocol level, and why does registration order decide who can attack whom?**

At the raw protocol level, ASGI middleware is an asynchronous callable that accepts three arguments: `scope` (a dict describing the connection — type, path, headers), `receive` (an async callable yielding incoming messages), and `send` (an async callable emitting outgoing messages). A raw middleware wraps the inner application by intercepting these callables.

`BaseHTTPMiddleware` from Starlette wraps that raw interface into something friendlier: it converts the scope/receive/send triplet into a `Request` object and a `call_next` coroutine. The `dispatch` method receives the `Request`, can act before calling `call_next(request)`, and can act again after receiving the `Response`.

When multiple middlewares are stacked, each wraps the one registered before it. `add_middleware` inserts at the front of the list, so the **last** registered ends up outermost — first on the request, last on the response. In this project that makes `GDPRLoggerMiddleware` the outer shell around `RequestLoggerMiddleware` and `AuthMiddleware` outer to `RateLimitMiddleware`. Ordering is a security-critical concern: authentication must precede rate limiting, because rate limiting an unauthenticated caller allows anonymous users to exhaust resource quotas.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
