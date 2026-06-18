# IS02P02 — MRL Benchmarker (Step 3: Slicing & Re-normalization)

> *"Most embedding models give you one fixed-size vector — use all 768 dimensions or none. Matryoshka Representation Learning changes the deal: the first k dimensions of an MRL embedding are themselves a valid, high-quality embedding. Train once. Truncate anywhere. Benchmark to find the smallest dimension that still meets your recall target."*

---

## What this project builds (Step 3)

In this third step, we implement vector truncation and verification logic:
1. **Declarative Settings (`config.py`)** — Loads configuration schemas (Ollama URL, model name) from host environment or `.env` files.
2. **Task Prefixes (`bench/embed.py`)** — Prepend model instruction labels (`search_document:` / `search_query:`) to align with target dual-encoder pathways.
3. **L2 Normalization & API Client (`bench/embed.py`)** — Requests dense embeddings from Ollama and scales output vectors to unit length ($L_2$ norm = $1.0$).
4. **MRL Truncation & Re-normalization (`bench/embed.py`)** — Truncates vectors to lower target dimensions and scales the truncated slice back to unit length ($L_2$ norm = $1.0$) to preserve cosine similarity calculations.

---

## Concepts Built So Far

### 1. Declarative Settings Validation
Utilizes Pydantic Settings to automatically parse, validate, and cast host configuration parameters into strict typed schemas.

### 2. Dual-Encoder Task Prefixes
Dual-encoder models use specialized semantic attention heads depending on the role. We prepend `search_document: ` for corpus index elements and `search_query: ` for user search queries to ensure high retrieval recall accuracy.

### 3. Cosine Dot-Product Equivalence
By L2-normalizing vectors to exactly $1.0$ magnitude during embedding, the cosine similarity equation collapses into a raw dot product:
$$\text{similarity}(\mathbf{u}, \mathbf{v}) = \mathbf{u} \cdot \mathbf{v}$$
This simplifies retrieval and search scoring down to a fast matrix multiplication.

### 4. Slicing Magnitudes & Re-normalization (The MRL Move)
When we truncate an embedding $\mathbf{v} \in \mathbb{R}^{768}$ to a smaller dimension $d$ (e.g. $256$), we discard the coordinate dimensions beyond $d$. This causes vector length decay:
$$\|\mathbf{v}_{\text{sliced}}\|_2 = \sqrt{\sum_{i=1}^{d} v_i^2} < 1.0$$
Because different coordinate values have different amounts of energy, each sliced vector decays by a different scalar factor. If we attempt dot-product comparisons on these raw slices, the scores are distorted by these varying vector lengths rather than reflecting true angular similarity.

To resolve this, we must re-normalize the vector back to unit length ($L_2$ norm = $1.0$) after truncation:
$$\mathbf{v}_{\text{truncated\_and\_normalized}} = \frac{\mathbf{v}_{\text{sliced}}}{\|\mathbf{v}_{\text{sliced}}\|_2}$$

This is the single most critical implementation step in MRL systems. Skipping re-normalization degrades retrieval accuracy.

---

## How to install & run

### 1. Model Server Setup
Ensure local Ollama is running and has the model pulled:
```bash
ollama pull nomic-embed-text
```

### 2. Environment Setup
Activate your environment:
```bash
source ~/venvs/is02p02-mrl-benchmarker/bin/activate
```

### 3. Run the Self-Test
Verify that truncation and re-normalization works correctly across multiple test texts and dimension sizes:
```bash
python -m bench.embed
```

Expected terminal output:
```text
Self-test: 5 texts x 5 dims = 25 norm checks

  OK  [document] 'The quick brown fox jumps over the lazy dog'  full=1.000000  dim64=1.000000  dim128=1.000000  dim256=1.000000  dim512=1.000000  dim768=1.000000
  OK  [document] 'Matryoshka embeddings store meaning in nested prefixes'  full=1.000000  dim64=1.000000  dim128=1.000000  dim256=1.000000  dim512=1.000000  dim768=1.000000
  OK  [query]    'How do I reduce memory usage in a vector database?'  full=1.000000  dim64=1.000000  dim128=1.000000  dim256=1.000000  dim512=1.000000  dim768=1.000000
  OK  [document] 'A REST API exposes resources over HTTP using GET and P'  full=1.000000  dim64=1.000000  dim128=1.000000  dim256=1.000000  dim512=1.000000  dim768=1.000000
  OK  [query]    'what is the best truncation dimension for retrieval?'  full=1.000000  dim64=1.000000  dim128=1.000000  dim256=1.000000  dim512=1.000000  dim768=1.000000

All norm checks passed. Truncation is sound.
```

---

## Project structure

```
is02p02-mrl-benchmarker/
  bench/
    __init__.py    Marks bench/ as a package directory
    embed.py       L2 normalization, embedding, truncation, and self-test suite
  config.py        Central settings loader singleton
```

---

## Algorithm & code flow

### 1. `_l2_normalize(vec)`
- **Input**: A 1-D numpy array.
- **Process**: Computes L2 norm. If `0.0`, returns `vec` unchanged. Otherwise, returns `vec / norm`.
- **Output**: Unit-length array ($L_2$ norm = $1.0$).

### 2. `embed(text, kind="document")`
- **Input**: String `text`, and role string `kind`.
- **Process**: Prepends role prefix. Sends to Ollama `/api/embeddings` POST request. Extracts output array, casts to float32, and runs `_l2_normalize`.
- **Output**: A float32 numpy array of shape `(768,)` ($L_2$ norm = $1.0$).

### 3. `truncate(vec, dim)`
- **Input**: Unit-length 1-D numpy array `vec`, and target dimension `dim`.
- **Process**: Slices the vector coords: `vec[:dim]`. Normalizes the sliced coordinates using `_l2_normalize`.
- **Output**: A float32 numpy array of shape `(dim,)` ($L_2$ norm = $1.0$).

---

## Observed

### Truncation Slicing Norms
By executing `python -m bench.embed`, we assert that every sliced embedding is placed back onto the unit sphere surface. Out of 25 distinct combinations of documents, queries, and dimension bounds (64, 128, 256, 512, 768), all L2 norms evaluate to exactly `1.000000` (within a tolerance threshold of `1e-5`).

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
