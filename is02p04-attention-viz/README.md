# IS02P04 — Attention Visualiser (Step 2)

> *"Each attention head asks: for this token, which other tokens are most relevant to my current purpose? Multiple heads attend to different linguistic relationships in parallel."*

This repository is Step 2 of the **Attention Visualiser** project in the Iron Stack curriculum.

---

## 2. What this step builds

In this step, we implement:
* **`attention_scratch.py`**: A clean PyTorch implementation of the **Scaled Dot-Product Attention** algorithm.
* **`kv_cache_calc.py`**: A VRAM profiler to calculate and report the exact memory footprint in gigabytes (GB) required by LLM Key-Value caches across different model sizes (Llama 1B to 405B) and context window lengths (1K to 128K tokens).

---

## 3. Core Concepts

### The KV Cache: Speed vs. Memory Cost
During the token-by-token (autoregressive) generation phase of a Decoder-only LLM, Key and Value vector representations for all past tokens do not change. To avoid redundant re-projections (which would scale computational cost quadratically as $O(N^2)$), models store past Key and Value vectors in a running cache. This reduces inference processing complexity to $O(N)$.

However, this speedup comes at a linear memory cost. The VRAM occupied by the cache is calculated as:
$$\text{Memory (Bytes)} = 2 \times \text{layers} \times \text{KV\_heads} \times \text{head\_dim} \times \text{seq\_len} \times \text{dtype\_bytes}$$

For large models running at long sequence contexts (e.g. 128K context), the KV Cache can consume hundreds of gigabytes of VRAM, often eclipsing the base footprint of the model parameter weights themselves.

---

## 4. How to Run

1. **Verify Attention Scratch Tests:**
   ```bash
   python attention_scratch.py
   ```

2. **Run the KV Cache Calculator Report:**
   ```bash
   python kv_cache_calc.py
   ```

---

## 5. Project Structure

```
is02p04-attention-viz/
├── attention_scratch.py
├── kv_cache_calc.py
└── README.md
```

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
