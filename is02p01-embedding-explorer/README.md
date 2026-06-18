# IS02P01 — Embedding Explorer (Step 3: Embedding Model Integration)

> *"An embedding is a claim about meaning made in the language of geometry. The model never sees a word — it sees a point in 384-dimensional space, and it judges closeness by the angle between points."*

---

## What this project builds (Step 3)

At this stage, we have integrated a local transformer model into our pipeline to generate real vector representations:
1. **Pure Python Vector Mathematics (`math_utils.py`)** — Standard library implementation of dot product, L2 norm, and cosine similarity.
2. **Custom Vector Database Engine (`store.py`)** — An in-memory vector storage registry utilizing parallel lists with strict dimension consistency checks.
3. **Model Integration & Controller (`main.py`)** — The `EmbeddingExplorer` controller which instantiates the `SentenceTransformer` model (`all-MiniLM-L6-v2`), generates 384-dimensional dense vectors, and coordinates insertion and querying.

No API server or dimensionality visualization layers are loaded yet.

---

## Concepts Built So Far

### 1. Semantic Embedding Spaces & all-MiniLM-L6-v2
Traditional string matching looks for identical characters. Embedding models map sentences onto a high-dimensional space (384 dimensions) where proximity correlates directly with semantic meaning. We use `all-MiniLM-L6-v2` because it runs quickly on standard consumer CPUs without requiring discrete GPU acceleration.

### 2. Mean Pooling
When a Transformer processes a sentence, it generates a representation vector for every single token (word/subword). To generate a single vector representing the entire sentence, the model performs **Mean Pooling**: it averages the token vectors together while taking the attention mask into account. The `sentence-transformers` library handles this automatically.

### 3. CPU Placement Guard (`device='cpu'`)
GPU library configurations can be inconsistent in shared development environments (like WSL/Windows). Loading weights directly to CPU ensures execution remains lightweight, deterministic, and uniform across all deployment platforms.

### 4. NumPy to Python Mapping (`.tolist()`)
Transformer models natively output embeddings as NumPy arrays. To keep our custom math functions in `math_utils.py` framework-agnostic, the controller maps the matrices back to native Python `list[float]` using `embeddings.tolist()`.

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
Run the main script as a module to seed the database with a 6-sentence corpus and execute semantic queries:
```bash
python -m explorer.main
```

##### Expected Output:
```text
=== Testing EmbeddingExplorer ===
Encoding and adding corpus...
Store loaded with 6 items.

Querying: 'Canines leaping over dogs'
  Rank 1: Score 0.5751 -> A fast canine leaps across a sleepy pup.
  Rank 2: Score 0.4709 -> The quick brown fox jumps over the lazy dog.

Querying: 'System data routing pipelines'
  Rank 1: Score 0.8053 -> Data pipelines route records between services.
  Rank 2: Score 0.4196 -> Information flow architecture defines how data moves.
=== Checks complete ===
```

---

## Project structure

```
is02p01-embedding-explorer/
  explorer/
    __init__.py    Exposes public package interface
    math_utils.py  Pure Python dot product, L2 norm, and cosine similarity
    store.py       Custom in-memory VectorStore database engine
    main.py        EmbeddingExplorer controller bridging model and store
  requirements.txt Specifies project dependencies
```

---

## Algorithm & code flow

### 1. `explorer/main.py` — EmbeddingExplorer
- `__init__(model_name)`: Loads the target SentenceTransformer on `device='cpu'` and initializes an empty `VectorStore`.
- `encode(texts)`: Generates 384-dimensional dense vectors and converts the NumPy outputs into standard Python float lists using `.tolist()`.
- `add(text)`: Encodes a text string, ensures it is a flat list of floats, and saves it in the store.
- `search(query, top_k)`: Encodes the query string and performs a cosine-similarity search against all indexed items, returning the top $K$ ranked hits.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
