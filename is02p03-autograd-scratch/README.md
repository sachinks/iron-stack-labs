# IS02P03 — Autograd Scratch (Step 1: Manual Tensor XOR Solver)

> *"Under the hood of every deep learning framework lies a dynamic computational graph. Every forward operation constructs the graph; every backward call traverses it in reverse topological order. To truly master neural networks, we must peel back the layers of abstraction: no torch.nn, no torch.optim. Just raw tensors, manual parameter updates, and explicit gradient resets."*

---

## What this project builds (Step 1)

In this first step, we implement a 2-layer Perceptron to solve the non-linear XOR classification problem using raw PyTorch tensors:
1. **Raw Parameter Initialization** — Explicitly defines weight matrices ($W_1$, $W_2$) and bias vectors ($b_1$, $b_2$) with `requires_grad=True` to register them as leaves of the computational graph.
2. **Explicit Activation Operations** — Implements custom `relu` and `sigmoid` functions directly.
3. **Define-by-Run Forward Path** — Projects 2D inputs into an 8D representation space and performs predictions using raw tensor matrix multiplications (`@`) and broadcasting additions.
4. **Manual SGD Optimization** — Performs weight optimization updates in a `torch.no_grad()` context block and manually resets parameter gradients to zero after each epoch.

---

## Concepts Built So Far

### 1. XOR Non-linear Space Warping
A single linear layer can only draw a straight line boundary, which is mathematically incapable of separating the XOR inputs:
* `(0, 0) -> 0`
* `(0, 1) -> 1`
* `(1, 0) -> 1`
* `(1, 1) -> 0`

By constructing a hidden layer that projects the inputs into an 8-dimensional space and applying a non-linear activation (ReLU), we warp the coordinate space. This lets the second linear projection separate the classes with a single hyperplane.

### 2. Gradient Accumulation Rule
In PyTorch, calling `loss.backward()` traverses the computational graph and **accumulates** (adds) gradients into the parameters' `.grad` attribute:
$$\text{p.grad} \leftarrow \text{p.grad} + \text{incoming\_gradient}$$
Accumulation is required to handle variables that participate in multiple independent computational pathways (like shared weights in RNNs). Because gradients accumulate by addition, we must explicitly reset them to zero (`p.grad.zero_()`) at the end of each training step.

### 3. The `no_grad` Parameter Update
When updating weights manually via SGD:
$$W \leftarrow W - \eta \cdot \frac{\partial L}{\partial W}$$
This subtraction is tracked as a mathematical operation by PyTorch if it involves tensors with `requires_grad=True`. To prevent PyTorch from appending the update step to the parameter's graph history—which would lead to infinite loop memory leaks and backpropagation failure—we must perform the update within a `with torch.no_grad():` block.

### 4. Dead-ReLU Avoidance
When a hidden unit's input $z$ is negative for all dataset samples, the ReLU activation outputs a flat $0.0$. Since the local gradient is $0.0$, no gradient propagates back through this unit:
$$\frac{\partial L}{\partial W} = 0$$
The neuron is "dead" and cannot recover. A 4-neuron hidden layer has a $\sim 40\%$ chance of hitting a dead-neuron configuration that stalls training. Increasing the hidden layer width to 8 provides redundant capacity to guarantee convergence on every random seed.

---

## How to install & run

### 1. Environment Setup
Create a native WSL virtual environment:
```bash
python3 -m venv ~/venvs/is02p03-autograd-scratch
source ~/venvs/is02p03-autograd-scratch/bin/activate
```

### 2. Install PyTorch (CPU-only)
Install the CPU-only wheels (this prevents downloading massive CUDA libraries that degrade NTFS-mounted directory operations):
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 3. Run the XOR Solver
Verify convergence by running the script:
```bash
python xor_solver.py
```

Expected output:
```text
epoch    0  loss=0.8123
epoch  200  loss=0.4859
epoch  400  loss=0.2976
epoch  600  loss=0.1068
epoch  800  loss=0.0601
epoch 1000  loss=0.0412
epoch 1200  loss=0.0315
epoch 1400  loss=0.0257
epoch 1600  loss=0.0218
epoch 1800  loss=0.0189

final loss = 0.0167

Final predictions (probability that output == 1):
  [0.0, 0.0] -> 0.020  (rounds to 0, target 0)  OK
  [0.0, 1.0] -> 0.981  (rounds to 1, target 1)  OK
  [1.0, 0.0] -> 0.980  (rounds to 1, target 1)  OK
  [1.0, 1.0] -> 0.021  (rounds to 0, target 0)  OK
```

---

## Project structure

```
is02p03-autograd-scratch/
  xor_solver.py     2-layer Perceptron manual XOR solver using raw PyTorch tensors
  README.md         Step-specific implementation notes and theory
```

---

## Algorithm & code flow

### 1. `relu(x)`
- **Input**: PyTorch Tensor of any shape.
- **Process**: Clamps negative elements to 0: `torch.clamp(x, min=0.0)`.
- **Output**: Clamped tensor of identical shape.

### 2. `sigmoid(x)`
- **Input**: PyTorch Tensor of any shape.
- **Process**: Squashes values into (0, 1): `1.0 / (1.0 + torch.exp(-x))`.
- **Output**: Probabilistic squashed tensor of identical shape.

### 3. `forward(x)`
- **Input**: Dense input tensor `(4, 2)`.
- **Process**:
  1. Compute linear hidden projections: `z1 = x @ W1 + b1` `(4, 8)`.
  2. Apply non-linear activation: `a1 = relu(z1)`.
  3. Compute linear output projections: `z2 = a1 @ W2 + b2` `(4, 1)`.
  4. Squish outputs: `sigmoid(z2)`.
- **Output**: Predictions matrix `(4, 1)`.

### 4. `bce_loss(y_hat, y_true)`
- **Input**: Predicted probabilities `y_hat` and binary targets `y_true`.
- **Process**: Computes binary cross-entropy with a minor epsilon stability clamp `eps=1e-7` inside logarithmic functions to avoid `-inf` outputs.
- **Output**: Scalar tensor loss.

### 5. `train()`
- **Input**: Epochs, inputs, targets, and learning rate.
- **Process**:
  1. Forward Pass to build dynamic DAG graph.
  2. `loss.backward()` to run reverse backpropagation.
  3. In-place parameter optimization updates inside `torch.no_grad()`.
  4. Manual gradient zeroing on all parameters.

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
