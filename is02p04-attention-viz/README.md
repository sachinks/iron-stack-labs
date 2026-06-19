# IS02P04 — Attention Visualiser (Step 3)

> *"Each attention head asks: for this token, which other tokens are most relevant to my current purpose? Multiple heads attend to different linguistic relationships in parallel."*

This repository is Step 3 of the **Attention Visualiser** project in the Iron Stack curriculum.

---

## 2. What this step builds

In this step, we implement:
* **`attention_scratch.py`**: A clean PyTorch implementation of the **Scaled Dot-Product Attention** algorithm.
* **`kv_cache_calc.py`**: A VRAM profiler to calculate and report LLM Key-Value cache requirements.
* **`context_placement.py`**: A production-grade implementation of the interleaving algorithm designed to order retrieved database chunks such that high-scoring chunks occupy the high-attention boundaries (start and end) of a context prompt, leaving lower-scoring chunks in the middle.

---

## 3. Core Concepts

### Lost-in-the-Middle Phenomenon
Large language models do not process long contexts uniformly. Retrieval accuracy is typically excellent at the start and end of a context window, but exhibits a 30% to 40% degradation in the middle. 

### Interleaving Optimization
To mitigate this positional bias, we place the most relevant context blocks at the boundaries. If we have $k$ chunks sorted descending by relevance score, we layout them in an alternating front/back sequence:
1. Rank 1 $\rightarrow$ Start (Position 1)
2. Rank 2 $\rightarrow$ End (Position $k$)
3. Rank 3 $\rightarrow$ Position 2
4. Rank 4 $\rightarrow$ Position $k-1$
5. ... and so on.

This guarantees that the highest-scoring chunk occupies index 0 (maximum attention) and the second-highest occupies the final index (also high attention), while weaker context elements are safely buried in the lower-attention middle region.

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

3. **Verify Context Placement Interleaving:**
   ```bash
   python context_placement.py
   ```

---

## 5. Project Structure

```
is02p04-attention-viz/
├── attention_scratch.py
├── context_placement.py
├── kv_cache_calc.py
└── README.md
```

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
