# IS02P04 — Attention Visualiser (Step 4)

> *"Each attention head asks: for this token, which other tokens are most relevant to my current purpose? Multiple heads attend to different linguistic relationships in parallel."*

This repository is Step 4 of the **Attention Visualiser** project in the Iron Stack curriculum.

---

## 2. What this step builds

In this step, we implement:
* **`attention_scratch.py`**: A clean PyTorch implementation of the **Scaled Dot-Product Attention** algorithm.
* **`kv_cache_calc.py`**: A VRAM profiler to calculate and report LLM Key-Value cache requirements.
* **`context_placement.py`**: A production-grade implementation of the interleaving algorithm.
* **`placement_experiment.py`**: A tester that empirically measures retrieval performance under a ~4000-character context window. It places a key fact ("needle") at the start, middle, and end positions and queries a local Ollama server running `llama3.2` to check accuracy across multiple trials.

---

## 3. Core Concepts

### Empirical Needle-in-a-Haystack Testing
To verify the Lost-in-the-Middle hypothesis, we configure a controlled experiment:
* **Needle**: `"The capital of the Iron Stack project is Bengaluru."`
* **Filler**: 130 repetitions of the phrase `"The sky is blue. Water is wet. "` to generate a padding context of ~4000 characters (~1000 tokens).
* **Evaluation**: We run 10 queries per position (start, middle, end) at zero temperature. This lets us verify whether modern small language models (like `llama3.2` 3B) suffer from boundary bias at standard sequence lengths.

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

4. **Run the Lost-in-the-Middle Experiment:**
   Ensure Ollama is running (`ollama serve`) and the model is downloaded (`ollama pull llama3.2`), then run:
   ```bash
   python placement_experiment.py
   ```

---

## 5. Project Structure

```
is02p04-attention-viz/
├── attention_scratch.py
├── context_placement.py
├── kv_cache_calc.py
├── placement_experiment.py
└── README.md
```

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
