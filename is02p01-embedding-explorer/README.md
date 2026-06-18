# IS02P01 — Embedding Explorer (Step 4: Dimensionality Reduction with UMAP)

> *"An embedding is a claim about meaning made in the language of geometry. The model never sees a word — it sees a point in 384-dimensional space, and it judges closeness by the angle between points."*

---

## What this project builds (Step 4)

At this stage, we have integrated UMAP dimensionality reduction to visualize our embedding space:
1. **Pure Python Vector Mathematics (`math_utils.py`)** — Standard library implementation of dot product, L2 norm, and cosine similarity.
2. **Custom Vector Database Engine (`store.py`)** — An in-memory vector storage registry utilizing parallel lists with strict dimension consistency checks.
3. **Model Integration & Controller (`main.py`)** — The `EmbeddingExplorer` controller which instantiates the `SentenceTransformer` model (`all-MiniLM-L6-v2`), generates 384-dimensional dense vectors, and coordinates insertion and querying.
4. **UMAP Projection & Plotting (`visualise.py`)** — Uses UMAP to reduce the high-dimensional vectors to 2D coordinates and Matplotlib to save a dark-themed scatter plot (`embedding_space.png`), highlighting semantic topic clustering.

No FastAPI HTTP endpoints are loaded yet.

---

## Concepts Built So Far

### 1. High-Dimensionality Projection (PCA vs. UMAP)
* **PCA (Principal Component Analysis)** is a linear method that projects data onto the directions of maximum variance. It prioritizes global distance, often blurring local clusters.
* **UMAP (Uniform Manifold Approximation and Projection)** is a non-linear method that preserves local neighborhood structures. If points are close in 384D, UMAP maintains their closeness in 2D.
* **UMAP Interpretation Rule:** Distance in UMAP is *relative, not absolute*. Trust the clusters and neighbors, not the absolute coordinates.

### 2. Semantic Failure Modes Visible in UMAP
* **Sports Cluster Disconnection:** The model maps semantic relationships rather than abstract taxonomic classification. Sentences like *"The cricket team won the match"* and *"Marathon runners train for months"* share no vocabulary, so they scatter apart.
* **The Polysemy Collision:** The token *python* has double meanings (snake vs. language). Because of static token contributions, snake sentences like *"A python is a large snake that squeezes its prey"* get pulled towards the programming cluster.
* **Register Bias:** The model often weights style (register/tone) over topic. For a query like *"I enjoy programming"*, the casual tone forces it closer to *"Cats are wonderful pets"* than to a technical sentence like *"Git tracks changes across versions of source code."*

---

## How to install & run

### 1. Environment Setup
Create and activate your virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
Install CPU-only PyTorch first (to prevent downloading bulky CUDA libraries), then install the rest of the packages:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### 3. Run the Main Script
Run the main script as a module to seed the database with a 24-sentence corpus, execute queries, and generate the UMAP visualization:
```bash
python -m explorer.main
```

This will print search results demonstrating the polysemy collision and register bias, and save `embedding_space.png` in your project folder.

---

## Project structure

```
is02p01-embedding-explorer/
  explorer/
    __init__.py    Exposes public package interface
    math_utils.py  Pure Python dot product, L2 norm, and cosine similarity
    store.py       Custom in-memory VectorStore database engine
    main.py        EmbeddingExplorer controller seeding the 24-sentence corpus
    visualise.py   UMAP dimensionality reduction and Matplotlib plotting
  requirements.txt Specifies project dependencies
```

---

## Algorithm & code flow

### 1. `explorer/visualise.py`
- `visualise(store, output_path="embedding_space.png", groups=None)`:
  1. Pulls all embeddings and stacks them into a NumPy array. Raises `ValueError` if size is $< 3$.
  2. Caps `n_neighbors = min(15, n - 1)` to prevent UMAP crashes on small corpuses.
  3. Fits `umap.UMAP(n_components=2, random_state=42, n_neighbors=n_neighbors, min_dist=0.1, metric="cosine")` and transforms to shape `(n, 2)`.
  4. Plots points with a dark theme (`facecolor="#0D1117"`). Colors points by group using `tab10` colors if `groups` is provided, otherwise defaults to Indigo `#818CF8`.
  5. Annotates each point with its truncated text and saves the PNG.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
