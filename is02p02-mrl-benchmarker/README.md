# IS02P02 — MRL Benchmarker (Step 5: Benchmarking & Recall@K)

> *"Most embedding models give you one fixed-size vector — use all 768 dimensions or none. Matryoshka Representation Learning changes the deal: the first k dimensions of an MRL embedding are themselves a valid, high-quality embedding. Train once. Truncate anywhere. Benchmark to find the smallest dimension that still meets your recall target."*

---

## What this project builds (Step 5)

In this fifth step, we implement the metric calculation and benchmark sweep:
1. **Declarative Settings (`config.py`)** — Loads configuration schemas (Ollama URL, model name) from host environment or `.env` files.
2. **Task Prefixes (`bench/embed.py`)** — Prepend model instruction labels (`search_document:` / `search_query:`) to align with target dual-encoder pathways.
3. **L2 Normalization & API Client (`bench/embed.py`)** — Requests dense embeddings from Ollama and scales output vectors to unit length ($L_2$ norm = $1.0$).
4. **MRL Truncation & Re-normalization (`bench/embed.py`)** — Truncates vectors to lower target dimensions and scales the truncated slice back to unit length ($L_2$ norm = $1.0$) to preserve cosine similarity calculations.
5. **Corpus & Query Definition (`bench/corpus.py`)** — Defines a balanced testing dataset of 35 documents across 6 distinct topics, 9 evaluation search queries, and a dictionary of known-relevant document mappings used to sanity-check the full-dimensional embeddings baseline.
6. **Benchmarking Suite (`bench/benchmark.py`)** — Performs a sweep over candidate dimensions (64, 128, 256, 512, 768), calculating semantic similarity rankings using vectorized matrix operations, checking baseline sanity, and outputting recall@5, search latency, and memory footprints.

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

### 5. Balanced Evaluation Corpus and Sanity Checks
* **Class Balance:** To ensure that retrieval metrics are unbiased, our test dataset represents multiple categories with equal distribution (6 documents per topic across programming, finance, cooking, animals, sports, and health).
* **Baseline Sanity Validation:** Before performing dimension benchmarking, a `SANITY` map is utilized to test high-intent query matches against known relevant document targets in the full-dimensional space. If our system fails to return these targets at Rank 1, it implies that the indexing or prefix configuration is corrupted.

### 6. Evaluation Metrics: Recall@K, Latency, and Memory Footprint
* **Recall@K Metric:** Treats the full-dimensional ranking as the ground truth ("Gold Set"). It counts what proportion of those top-K results are preserved after truncation:
  $$\text{Recall@K} = \frac{|\text{TopK}_{\text{truncated}} \cap \text{TopK}_{\text{gold}}|}{K}$$
* **Vectorized Similarity Scoring:** Computes cosine similarities simultaneously for all documents by stacking normalized vectors into a 2D matrix $D \in \mathbb{R}^{N \times d}$ and calculating `D @ q` using optimized linear algebra operations.
* **Memory Footprint:** Measures bytes required to store embeddings in memory. Since each coordinate is a 32-bit float (4 bytes), storage scales linearly with dimension.

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

### 4. Verify Corpus Statistics
Verify the evaluation corpus and query dataset structure:
```bash
python -m bench.corpus
```

### 5. Run the Benchmarks
Run the full MRL sweep and output the comparison table:
```bash
python -m bench.benchmark
```

Expected output:
```text
Embedding 35 docs + 9 queries at full dim (once)...

Sanity check (full-dim top-1 vs known-relevant):
  [OK ] 'how do I catch and handle errors in my code...' -> p1 (want ['p1'])
  [OK ] 'ways to roll back changes in version control...' -> p2 (want ['p2'])
  [OK ] 'how to grow my long-term savings...' -> f1 (want ['f1', 'f5'])
  [OK ] 'how much sleep should I get...' -> h2 (want ['h2'])
  => reference looks sane

Results (k=5, corpus=35 docs):
  dim |  recall@5 |  search ms |  memory KB
----------------------------------------------
   64 |     0.822 |     0.0021 |        8.75
  128 |     0.911 |     0.0022 |       17.50
  256 |     0.978 |     0.0024 |       35.00
  512 |     1.000 |     0.0026 |       70.00
  768 |     1.000 |     0.0029 |      105.00
```

---

## Project structure

```
is02p02-mrl-benchmarker/
  bench/
    __init__.py    Marks bench/ as a package directory
    benchmark.py   Matrix scoring, metric calculations, and benchmarking loop
    corpus.py      Evaluation corpus, queries, and sanity-check mappings
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

### 4. `rank(query_vec, doc_matrix)`
- **Input**: A query vector `(dim,)` and document matrix `(n_docs, dim)`.
- **Process**: Vectorized dot product (`doc_matrix @ query_vec`) followed by sorting indices in descending order using `np.argsort(-scores)`.
- **Output**: Ranked document indices.

### 5. `recall_at_k(truncated_doc_vecs, truncated_query_vecs, gold, k)`
- **Input**: Truncated document and query matrices, ground truth top-k index sets `gold`, and integer `k`.
- **Process**: Calculates top-k rankings at the current dimension and averages the intersection ratios vs. `gold` over all queries.
- **Output**: Mean recall score.

---

## Observed

### Truncation Slicing Norms
By executing `python -m bench.embed`, we assert that every sliced embedding is placed back onto the unit sphere surface. Out of 25 distinct combinations of documents, queries, and dimension bounds (64, 128, 256, 512, 768), all L2 norms evaluate to exactly `1.000000` (within a tolerance threshold of `1e-5`).

### Retrieval Recall & Memory Sweep
Running the benchmark suite yields clear verification of the MRL capability:
* **Elbow Point (256 dimensions):** At just 256 dimensions, we reduce the embedding space and database memory footprint by **66.6%** (from 105.00 KB down to 35.00 KB) while preserving **97.8%** of the semantic retrieval accuracy (recall@5 = 0.978) relative to the full-dimensional 768-d reference model.
* **Latency Profile:** At 35 documents, latency is negligible ($<0.01$ ms) and dominated by Python runtime loop overhead, though memory savings map linearly to disk and memory caches.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
