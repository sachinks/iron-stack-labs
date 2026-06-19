# IS02P04 — Attention Visualiser (Step 1)

> *"Each attention head asks: for this token, which other tokens are most relevant to my current purpose? Multiple heads attend to different linguistic relationships in parallel."*

This repository is Step 1 of the **Attention Visualiser** project in the Iron Stack curriculum.

---

## 2. What this step builds

In this step, we implement:
* **`attention_scratch.py`**: A clean PyTorch implementation of the **Scaled Dot-Product Attention** algorithm. It handles batched multi-head tensors and supports causal masking (for autoregressive decoder models).

---

## 3. Core Concepts

### Scaled Dot-Product Attention
Attention allows representations to route information dynamically. The formula is:
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) V$$

* **Query ($Q$):** Represents what a token is looking for.
* **Key ($K$):** Represents what information a token holds/offers.
* **Value ($V$):** Contains the actual content representation aggregated into the final outputs.
* **Scaling Factor ($\sqrt{d_k}$):** Stabilizes gradients during training. Large $d_k$ causes dot products to grow large, pushing softmax into flat saturation zones with near-zero gradients. Dividing by $\sqrt{d_k}$ prevents this.

---

## 4. How to Run

Run the attention tests:
```bash
python attention_scratch.py
```

---

## 5. Project Structure

```
is02p04-attention-viz/
├── attention_scratch.py
└── README.md
```

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
