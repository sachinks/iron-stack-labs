# IS02P04 — Attention Visualiser

> *"Each attention head asks: for this token, which other tokens are most relevant to my current purpose? Multiple heads attend to different linguistic relationships in parallel."*

This repository is the final project of **Layer 2 (Representation and Similarity)** of the Iron Stack curriculum. It provides a comprehensive set of diagnostic scripts to implement scaled dot-product attention from scratch, profile the memory cost of KV caches, implement context placement heuristics, and visualize attention weight distributions in raw text sentences.

---

## 2. What this project builds

This project builds:
1. **`attention_scratch.py`**: A PyTorch implementation of the scaled dot-product attention formula with shape-verification tests and causal mask support.
2. **`kv_cache_calc.py`**: A VRAM profiler calculating the memory overhead of storing Key and Value activations during autoregressive generation.
3. **`context_placement.py`**: An interleaving chunk organizer designed to place highly relevant context segments at attention boundaries to mitigate the "Lost-in-the-Middle" retrieval drop.
4. **`placement_experiment.py`**: An empirical test runner demonstrating model retrieval performance based on needle position inside a 4000-character context window.
5. **`attention_viz.py`**: An attention visualizer exporting BertViz's interactive `head_view` and `model_view` plots to standalone HTML files.

---

## 3. Core Concepts

### Multi-Head Attention Mechanics
Attention determines the correlation between token representations. Rather than computing routing once, Multi-Head Attention projects input vectors into independent Query, Key, and Value ($Q, K, V$) spaces $H$ times in parallel. This allows different heads to simultaneously track separate linguistic patterns (e.g. syntactic, coreference, positional).

### Scaled Dot-Product Attention
Attention scores are computed as:
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V$$
Dividing by $\sqrt{d_k}$ ensures that for large dimensions, raw dot products do not grow too large and saturate the softmax function (which leads to vanishing gradients during training).

### The KV Cache Cost
During autoregressive generation, past token Key and Value representations are static. Storing them in a cache prevents re-projecting the entire historical prefix at every new generation step, reducing the projection complexity from $O(N^2)$ to $O(N)$ at the expense of linear GPU VRAM memory growth.

### Lost-in-the-Middle Phenomenon
Large language models tend to pay the highest attention to information located at the beginning and the end of the input context window. Information placed in the middle of long prompts exhibits a 30% to 40% retrieval degradation. Interleaving retrieved search results puts the highest-scoring context chunks at the boundaries and lowest-scoring chunks in the middle.

---

## 4. How to Install & Run

1. **Activate the Virtual Environment:**
   Ensure you are using native WSL Python 3.12:
   ```bash
   source ~/venvs/is02p04-attention-viz/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   ```

3. **Run Diagnostic and Verification Scripts:**
   - **Verify Attention Implementation:**
     ```bash
     python attention_scratch.py
     ```
   - **Profile KV Cache Footprint:**
     ```bash
     python kv_cache_calc.py
     ```
   - **Verify Context Placement Heuristic:**
     ```bash
     python context_placement.py
     ```
   - **Run Lost-in-the-Middle Experiment:**
     Ensure Ollama is running (`ollama serve`) and has `llama3.2` downloaded, then execute:
     ```bash
     python placement_experiment.py
     ```
   - **Generate Attention Visualizations:**
     ```bash
     python attention_viz.py
     ```
     Once completed, open `head_view.html` and `model_view.html` in any web browser to view the interactive D3.js visualization.

---

## 5. Project Structure

```
is02p04-attention-viz/
├── attention_scratch.py
├── attention_viz.py
├── context_placement.py
├── head_view.html (generated)
├── kv_cache_calc.py
├── model_view.html (generated)
├── notes.md
├── placement_experiment.py
└── README.md
```

---

## 6. Algorithm & Code Flow

### Scaled Dot-Product Attention Flow
* **Function Signature**: `attention(Q, K, V, mask=None)`
* **Inputs**:
  - `Q`: `(batch, heads, seq_len, d_k)`
  - `K`: `(batch, heads, seq_len, d_k)`
  - `V`: `(batch, heads, seq_len, d_v)`
  - `mask`: `(seq_len, seq_len)` or broadcastable shape.
* **Flow**:
  1. Calculate `scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)`
  2. If `mask` is provided, run `scores.masked_fill(mask == 0, -1e9)`
  3. Compute `weights = F.softmax(scores, dim=-1)`
  4. Compute output `output = torch.matmul(weights, V)`
  5. Return `output, weights`

---

## 7. Observed Results

### KV Cache Memory Scaling
For a sequence length of 131,072 (128K context) at float16 (2 bytes):
* **Llama 3.2 1B**: ~4.00 GB
* **Llama 3.2 3B**: ~14.00 GB
* **Llama 3.3 70B**: ~320.00 GB (Assuming standard MHA; GQA reduces this to ~40.00 GB by sharing KV heads)
* **Llama 3.1 405B**: ~1008.00 GB

At 128K context, Llama 405B's cache footprint surpasses 1 TB of VRAM, demonstrating why context-length serving is extremely memory-intensive.

### Needle-in-a-Haystack Results
Running the local `llama3.2` model at a 4000-character context window:
* **Start Position Accuracy**: 90%
* **Middle Position Accuracy**: 100%
* **End Position Accuracy**: 100%
* **Degradation**: -10%

Because `llama3.2` is a highly optimized lightweight model and the test sequence (approx. 1000 tokens) sits well within its native context capability, it achieves perfect retrieval at both the middle and end. 

### BertViz Attention Weight Visualisation
* **Early Layers**: Positional diagonals are highly visible, indicating tokens attend heavily to neighboring words.
* **Middle Layers**: Complex cross-word lines emerge representing syntactic bindings.
* **Late Layers**: The word `"it"` shows a concentrated focus on `"trophy"`, demonstrating successful semantic coreference resolution.

---

## 8. BENEATH

### What is the KV cache in a transformer model — what exactly does it store at each layer during autoregressive generation, why does it make inference significantly faster, and what is its memory cost as a function of sequence length and number of layers? How does this affect practical context window limits in production deployment?

The KV cache stores the Key ($K$) and Value ($V$) projected tensors computed for all previous tokens in a sequence across all layers of the Transformer. 

During the autoregressive generation of token $t$, the attention mechanism requires the similarity metrics between the new query $q_t$ and the historical keys $K_{1..t}$. If we do not store these keys, we must feed the entire historical prompt $x_{1..t}$ back through the network to re-derive the $K$ and $V$ activations for all past positions. 

By keeping a running cache:
1. We only project the single newly generated token $x_t$ through the layer weights to get $q_t, k_t, v_t$. This keeps the parameter projection cost flat at $O(1)$ operations per step.
2. We append $k_t$ and $v_t$ to the KV cache.
3. We compute the dot product between $q_t$ and the complete cached key matrix $K$, which scales at $O(t)$ operations.

This reduces the generation complexity of $n$ tokens from $O(n^2)$ model-parameter projection operations to $O(n)$ model-parameter projection operations, making inference substantially faster.

The memory cost in bytes scales as:
$$\text{Memory} = 2 \times \text{layers} \times \text{KV\_heads} \times \text{head\_dim} \times \text{seq\_len} \times \text{dtype\_bytes}$$

Because this footprint grows linearly with sequence length and batch size, long-context serving consumes massive portions of GPU VRAM. When serving a model, the constant weights of the model plus the expanding KV cache must fit in memory. If they exceed VRAM, the engine throws an Out of Memory (OOM) error. Consequently, the KV cache footprint is the primary limiting factor for maximum context windows and batch throughput, motivating modern memory management techniques like **PagedAttention** (which dynamically allocates non-contiguous cache blocks like OS virtual pages) and architecture optimizations like **Grouped-Query Attention (GQA)**.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
