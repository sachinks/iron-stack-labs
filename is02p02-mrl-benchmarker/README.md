# IS02P02 — MRL Benchmarker (Step 2: Task Prefixes & Embedding Normalization)

> *"The engineer who ships, measures, and fixes beats the engineer who only reads."*

---

## What this project builds (Step 2)

In this second step, we build the core embedding and normalization library:
1. **Declarative Settings (`config.py`)** — Uses Pydantic Settings to load environment configuration from `.env` files or system environment variables with type validation.
2. **Retrieval Task Prefixes (`bench/embed.py`)** — Automatically prepends model task prefixes (`search_document:` and `search_query:`) to format text for the dual-encoder architecture.
3. **L2 Normalization & API Client (`bench/embed.py`)** — Sends text inputs to a local Ollama server, parses the resulting embedding vector, and normalizes the vector to unit length ($L_2$ norm = $1.0$).

---

## Concepts Built So Far

### 1. Declarative Settings Validation
Instead of using unsafe, typeless dictionary lookups via `os.environ.get()`, we define a schema class (`Settings`) utilizing Pydantic Settings. This ensures:
- **Type Casting & Safety** — Host environment strings are automatically cast to target Python types (e.g. string URL, float timeouts, integer dimensions).
- **Environment Isolation (`extra="ignore"`)** — Unknown variables present on the host OS are ignored to prevent runtime verification failures.
- **Global Singleton Pattern** — Configuration is initialized once at startup into a single instance (`settings`) shared by all modules.

### 2. Dual-Encoder Task Prefixes
Modern dual-encoder models (such as `nomic-embed-text`) process query and document texts through different semantic channels:
- Documents (the items being searched) are prefixed with `search_document: ` to build indexable representation tables.
- Queries (what a user inputs) are prefixed with `search_query: ` to optimize the vector for finding documents.
Omission of these task prefixes does not raise runtime errors but silently degrades retrieval recall accuracy.

### 3. Cosine Dot-Product Equivalence via L2 Normalization
Standard cosine similarity measures the angle between two vectors $\mathbf{u}$ and $\mathbf{v}$:
$$\text{cosine\_similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
By dividing every vector by its $L_2$ norm ($\|\mathbf{u}\|_2 = \sqrt{\sum u_i^2}$) at embedding time, we force their magnitudes to exactly $1.0$. Consequently, the similarity equation simplifies to a pure dot product:
$$\text{cosine\_similarity}(\mathbf{u}, \mathbf{v}) = \mathbf{u} \cdot \mathbf{v}$$
This collapses retrieval calculations down to a simple matrix multiplication (`docs @ query`), bypassing expensive square-root operations.

---

## How to install & run

### 1. Model Server Setup
Ensure a local [Ollama](https://ollama.com) instance is running and the target model is loaded:
```bash
ollama pull nomic-embed-text
```

### 2. Environment Setup
Create and activate your virtual environment:
```bash
python3 -m venv ~/venvs/is02p02-mrl-benchmarker
source ~/venvs/is02p02-mrl-benchmarker/bin/activate
```

### 3. Install Dependencies
Install packages:
```bash
pip install pydantic-settings requests numpy
```

### 4. Verify Step 2 Code
Run the embed module as a standalone script to execute its inline math normalization tests and verify local Ollama connectivity:
```bash
python -m bench.embed
```

Expected terminal output (assuming Ollama is running):
```text
Running inline tests for Step 2 math and structures...
  [OK] L2 normalization logic matches unit-length expectations.
  [OK] Zero-vector division guard behaves correctly.

Attempting connection to Ollama server...
  [OK] Successfully connected to Ollama!
  [OK] Generated vector shape: (768,)
  [OK] Generated vector L2 norm: 1.000000

Inline verification checks complete.
```

---

## Project structure

```
is02p02-mrl-benchmarker/
  bench/
    __init__.py    Marks bench/ as a package directory
    embed.py       L2 normalization and Ollama connection library
  config.py        Central settings loader singleton
```

---

## Algorithm & code flow

### 1. `_l2_normalize(vec)`
- **Input**: A 1-D numpy array `vec`.
- **Process**: Computes $\|\text{vec}\|_2$ via `np.linalg.norm(vec)`. If the norm is `0.0` (zero-vector guard), returns `vec` unmodified. Otherwise, divides the vector coordinates by the norm.
- **Output**: A new float32 array of unit length.

### 2. `embed(text, kind="document")`
- **Input**: A string `text`, and a string `kind` representing either `"document"` or `"query"`.
- **Process**: Prepend `search_document: ` or `search_query: ` based on `kind`. Make an HTTP POST request to `/api/embeddings` on the local Ollama server, parse the float list into a numpy array, and normalize it using `_l2_normalize`.
- **Output**: A float32 numpy array of shape `(768,)`.

---

## Observed

### Math Normalization Verification
When we run `python -m bench.embed`, the mathematical properties of the $L_2$ normalizer are validated:
1. Normalizing the 2D vector `[3.0, 4.0]` yields `[0.6, 0.8]` which has an exact norm of $1.0$.
2. The zero-vector edge case is handled without raising division-by-zero errors.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
