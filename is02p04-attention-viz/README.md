# IS02P04 — Attention Visualiser (Step 5)

> *"Each attention head asks: for this token, which other tokens are most relevant to my current purpose? Multiple heads attend to different linguistic relationships in parallel."*

This repository is Step 5 of the **Attention Visualiser** project in the Iron Stack curriculum.

---

## 2. What this step builds

In this step, we implement:
* **`attention_scratch.py`**: A clean PyTorch implementation of the **Scaled Dot-Product Attention** algorithm.
* **`kv_cache_calc.py`**: A VRAM profiler to calculate and report LLM Key-Value cache requirements.
* **`context_placement.py`**: A production-grade implementation of the interleaving algorithm.
* **`placement_experiment.py`**: A tester that empirically measures retrieval performance under a ~4000-character context window.
* **`attention_viz.py`**: A script that loads `bert-base-uncased` from Hugging Face and extracts multi-head attention weights. It uses the `html_action='return'` parameter in BertViz to export interactive `head_view` and `model_view` plots to standalone HTML pages (`head_view.html` and `model_view.html`).

---

## 3. Core Concepts

### Linguistic Head Specialisation
Transformer models route information by projecting input embeddings through multiple attention heads in parallel. Each head learns to specialize in detecting specific relationships:
1. **Positional / Adjacency (Early Layers 0–3)**: Attention weights exhibit a clean diagonal structure where tokens primarily pay attention to adjacent neighbors.
2. **Syntactic Binding (Middle Layers 4–8)**: Attention patterns connect syntactic dependencies (e.g. nouns attending to verbs, adjectives attending to nouns).
3. **Semantic / Coreference (Late Layers 9–12)**: Attention heads learn coreference patterns, mapping pronouns back to their antecedents. For example, in the sentence:
   > *"The trophy did not fit in the suitcase because it was too large."*
   The head in Layer 10/11 will attend heavily from `"it"` to `"trophy"`.

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
   ```bash
   python placement_experiment.py
   ```

5. **Generate HTML Visualizations:**
   ```bash
   python attention_viz.py
   ```
   Open `head_view.html` or `model_view.html` in a web browser to view the interactive D3.js attention diagrams.

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
├── placement_experiment.py
└── README.md
```

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
