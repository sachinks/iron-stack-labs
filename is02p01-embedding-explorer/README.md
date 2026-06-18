# IS02P01 — Embedding Explorer

> *"An embedding is a claim about meaning made in the language of geometry. The model never sees a word — it sees a point in 384-dimensional space, and it judges closeness by the angle between points. Everything an embedding gets right, and everything it gets wrong, follows from that one decision: meaning is a direction."*

---

## What this project builds

A small service that turns sentences into vectors, stores them in memory, and answers "what is most similar to this?" by cosine search. It also projects the invisible 384-dimensional space down to 2D with UMAP so the structure — and the failures — become visible. The whole thing is wrapped in a FastAPI service so the embedding engine runs as a long-lived process that other programs can query over HTTP.

The XOR problem in this layer is: computers cannot compare the *meaning* of two sentences directly. This project is the foundation for everything in Layer 3 (retrieval) and Layer 4 (agents) — those systems only work because embeddings give us a geometry of meaning to search over.

---

## Why embeddings

A computer cannot compare the meaning of two sentences directly. Strings support only exact or substring matching — "I enjoy programming" and "I love writing code" share almost no characters yet mean nearly the same thing, while "I enjoy programming" and "I enjoy gardening" share most words yet mean different things. Keyword matching is blind to this.

An embedding model solves it by mapping text to a fixed-length vector of floating-point numbers, trained so that texts with similar meaning land close together in the vector space. Comparison of meaning becomes comparison of geometry — and geometry is something a computer does trivially and fast.

---

## Vector space and dimensionality

`all-MiniLM-L6-v2` produces a **384-dimensional** vector for any input text. Each dimension is a learned axis of variation — no single axis is human-interpretable ("dimension 57" is not "formality"), but collectively the 384 numbers position the text relative to everything the model saw in training.

Why 384 and not 2 or 2,000? Capacity. Two dimensions cannot keep "finance," "cooking," "animals," and "code" all mutually distinguishable — there is not enough room, and unrelated concepts get forced together. Thousands of dimensions capture more nuance but cost more memory and compute per comparison, with diminishing returns. 384 is the model's chosen trade-off between expressiveness and cost.

The catch: 384 dimensions cannot be seen directly. That is what UMAP is for.

---

## Cosine similarity

Similarity here is the **cosine of the angle** between two vectors — direction, not magnitude. Two sentences about the same topic point the same way regardless of length or word count.

Because every vector is **L2-normalised at encode time** (`normalize_embeddings=True` implicitly or handled via explicit code), each one has length 1. For unit vectors, cosine similarity reduces to a plain **dot product** — which is exactly what `VectorStore.search()` computes:

```python
matrix = np.array(self._embeddings)   # (n, 384)
q      = np.array(query_embedding)    # (384,)
scores = np.dot(matrix, q)            # (n,) — one cosine score per stored text
```

One matrix-vector multiply scores the entire store at once. Scores run roughly 1.0 (identical direction) down toward 0 (unrelated). Sorting descending gives the ranking.

---

## UMAP — seeing the unseeable

UMAP (Uniform Manifold Approximation and Projection) squashes 384-d vectors to 2-d for plotting while trying to keep near-neighbours near. It builds a graph of each point's nearest neighbours in the high-dimensional space, then lays that graph out in 2-d so the local structure survives.

Two parameters matter here:

- **`n_neighbors`** — how much local vs global structure to preserve. Must be smaller than the point count, so the code caps it: `n_neighbors = min(15, n - 1)`. Without that guard, small corpora crash.
- **`random_state=42`** — UMAP is stochastic; fixing the seed makes the layout reproducible across runs.

UMAP distances are **relative, not absolute** — read clusters and neighbours, not exact coordinates. Rendering uses `matplotlib.use("Agg")` so it works headless under WSL (writes to PNG, no GUI needed).

---

## How to install & run

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 3. Run the script (embed, search, visualise — prints results + saves PNG)
python -m explorer.main

# 4. Run the API server
uvicorn explorer.api:app --reload
# then open http://127.0.0.1:8000/docs
```

On first run, `all-MiniLM-L6-v2` (~90 MB) downloads automatically from HuggingFace.

---

## Project structure

```
is02p01-embedding-explorer/
  explorer/
    __init__.py    Exposes public package interface
    math_utils.py  Pure Python dot product, L2 norm, and cosine similarity
    store.py       Custom in-memory VectorStore database engine
    main.py        EmbeddingExplorer + CORPUS (24 sentences, 6 topics)
    visualise.py   UMAP 384d → 2d, colour-by-topic, saves PNG
    api.py         FastAPI app — /embed /search /visualise /health
  requirements.txt Specifies project dependencies
```

---

## Algorithm & code flow

### 1. `explorer/main.py` — EmbeddingExplorer

`EmbeddingExplorer.__init__` loads `all-MiniLM-L6-v2` once via `SentenceTransformer` and initialises an empty `VectorStore`. The class has three public methods:

**`encode(text) -> list[float]`** — the single encoding entry point. Calls `self.model.encode(text)`. `.tolist()` converts the numpy float32 array to a plain Python list for storage and JSON serialisation. Both `add()` and `search()` delegate here.

**`add(text) -> list[float]`** — calls `self.encode(text)`, passes the result to `self.store.add(text, embedding)`, and **returns the embedding**. Returning it means the `/embed` endpoint can include the vector in its response without a second encode call.

**`search(query, top_k=5) -> list[dict]`** — calls `self.encode(query)`, passes the result to `self.store.search(q_emb, top_k)`, and returns the ranked list.

### 2. `explorer/store.py` — VectorStore

`VectorStore` maintains two parallel lists: `_texts` (strings) and `_embeddings` (lists of floats). All embeddings are assumed unit-length — the store does **not** normalise for you.

- **`add(text, embedding)`** — validation checks on dimensions, then `list.append()` to both lists.
- **`search(query_emb, top_k=5) -> list[dict]`** — guards against an empty store, then computes `cosine_similarity` for each stored item, sorts descending, and returns top-k results.

### 3. `explorer/visualise.py` — UMAP projection

- Computes `n_neighbors = min(15, n - 1)` to guard UMAP against small corpora.
- Fits UMAP reducer and transforms to `(n, 2)`.
- Plots points with a dark theme (`facecolor="#0D1117"`). Colors points by group using `tab10` colors if `groups` is provided, otherwise defaults to Indigo `#818CF8`. Annotates each point with its truncated text and saves to file.

### 4. `explorer/api.py` — FastAPI service

- **Shared state.** A module-level `state: dict = {}` holds the single `EmbeddingExplorer` instance and the `groups` list.
- **`lifespan` hook.** On startup: instantiates `EmbeddingExplorer()`, calls `explorer.add(text)` for all 24 CORPUS sentences, and stores `state["explorer"]` and `state["groups"]`. On shutdown: clears state.

| Endpoint | Behaviour |
|---|---|
| `GET /health` | `{"status": "ok", "store_size": len(state["explorer"].store)}` |
| `POST /embed` | Calls `explorer.add(req.text)`, appends `"user"` to `state["groups"]`, returns `{"added", "store_size", "embedding"}` |
| `POST /search` | Calls `explorer.search(req.query, req.top_k)`, returns `{"query", "results"}` |
| `GET /visualise` | Calls `visualise(explorer.store, groups=state["groups"])`, returns `FileResponse("embedding_space.png", media_type="image/png")` |

---

## Observed

Running the 24-sentence corpus and projecting it reveals real structure and real failure.

**Clusters that formed:** finance, cooking, animals, and weather each grouped cleanly — their members share vocabulary and register.

**Sports did NOT cluster.** "The cricket team won the match in the final over," "She scored a stunning goal in the last minute," and "Marathon runners train for months before the race" scattered apart. They share little surface wording, and the model keys on wording.

**The polysemy collision.** "A python is a large snake that squeezes its prey" sits visibly pulled toward the programming cluster — the token *python* carries both senses, and the static embedding cannot tell which one this sentence means.

**The register failure — the headline result.** Query: "I enjoy programming in python"

| Rank | Score | Text |
|------|-------|------|
| 1 | 0.8011 | Python is a high-level programming language. |
| 2 | 0.6038 | I love writing code and building software. |
| 3 | 0.4360 | A python is a large snake that squeezes its prey. |

---

## BENEATH

**What does the 384-dim vector actually encode, why does cosine similarity measure meaning, and why do embeddings systematically reward register over topic?**

A sentence embedding is the model's compressed summary of a sentence, produced by a transformer encoder. Each token is first mapped to a vector; self-attention then lets every token's representation absorb context from the others; the per-token vectors are pooled (mean pooling for MiniLM) into one fixed 384-d vector. The 384 numbers are **learned coordinates** — directions in a space the model shaped during contrastive training, where it was pushed to place paraphrase pairs close and unrelated pairs far apart. No dimension is individually meaningful; meaning lives in the *direction* of the whole vector. That is the core claim of embeddings: meaning is a direction, similarity is an angle.

Cosine similarity works because the training objective *was* an angular objective. Contrastive losses optimise dot-product / cosine similarity between normalised vectors directly — so the geometry the model learned is exactly the geometry we query with. Normalising to unit length at encode time makes cosine collapse to a single dot product and makes magnitude irrelevant: only direction (meaning) counts, not vector length (which correlates with incidental things like token count).

The register bias is a direct consequence of what signal dominates the gradient during training. Surface features — word choice, phrasing, grammatical person, affective tone — are dense, high-frequency signals; abstract topical equivalence ("git and kubernetes are both software infrastructure") is a sparse, higher-order signal that appears far less often in paraphrase-style training pairs. So the embedding encodes *how something is said* at least as strongly as *what is said*.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
