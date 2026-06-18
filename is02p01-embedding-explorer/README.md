# IS02P01 — Embedding Explorer (Step 2: Vector Store Baseline)

> *"An embedding is a claim about meaning made in the language of geometry. The model never sees a word — it sees a point in high-dimensional space, and it judges closeness by the angle between points."*

---

## What this project builds (Step 2)

At this stage, we have implemented the custom backend foundation of our embedding search system:
1. **Pure Python Vector Mathematics (`math_utils.py`)** — Standard library implementation of dot product, L2 norm (magnitude), and cosine similarity.
2. **Custom Vector Database Engine (`store.py`)** — An in-memory vector storage registry utilizing parallel lists with strict dimension consistency checks.

No external machine learning libraries or API routes are loaded yet. This represents the raw mathematical and architectural plumbing required to index and query vector spaces.

---

## Concepts Built So Far

### 1. Cosine Similarity vs. Dot Product
To search for semantically related documents, we measure the angle $\theta$ between vectors rather than their absolute distance. 
* **Dot Product ($\mathbf{u} \cdot \mathbf{v}$)** is affected by both the directions and the magnitudes of the vectors.
* **Cosine Similarity** normalization scales the vectors to strip out magnitude variations (such as differences in sentence length or word frequency):
$$\text{Cosine Similarity}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$

### 2. Validation Guards
* **The Zero-Vector Trap** — If a vector has a magnitude of `0.0`, computing similarity triggers a division-by-zero error. `cosine_similarity` checks this and raises a `ValueError`.
* **Dimension Guard** — A vector database cannot compare vectors of different lengths. Our `VectorStore` checks and enforces that every vector inserted (and every query) matches the dimension of the first indexed vector.

---

## How to install & run

### 1. Environment Setup
Create and activate your virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Run Sanity Checks
Since there is no active server or ML model yet, you can test the underlying math and vector store by running the modules directly:

```bash
# Verify vector math operations (identical, orthogonal, opposite vectors & guards)
python -m explorer.math_utils

# Verify vector store operations (dimension checks, sorting, empty store checks)
python -m explorer.store
```

---

## Project structure

```
is02p01-embedding-explorer/
  explorer/
    __init__.py    Exposes public package interface
    math_utils.py  Pure Python dot product, L2 norm, and cosine similarity
    store.py       Custom in-memory VectorStore database engine
```

---

## Algorithm & code flow

### 1. `explorer/math_utils.py`
- `dot_product(u, v)`: Returns $\sum u_i v_i$. Raises `ValueError` on empty input or dimension mismatch.
- `l2_norm(u)`: Returns $\sqrt{\sum u_i^2}$. Raises `ValueError` on empty input.
- `cosine_similarity(u, v)`: Returns $\frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$. Raises `ValueError` if either vector has an L2 norm of `0.0`.

### 2. `explorer/store.py`
- `VectorStore.add(text, embedding)`: Validates that the embedding is not empty, matches the current database dimension, and appends the values to internal parallel lists (`self._texts` and `self._embeddings`).
- `VectorStore.search(query_embedding, top_k=5)`: Computes similarity scores for all stored vectors, sorts them in descending order, and returns the top results formatted as a list of dictionaries with ranks, rounded scores, and texts.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
