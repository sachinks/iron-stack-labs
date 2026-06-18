# IS02P02 — MRL Benchmarker (Step 1: Configuration & Settings Setup)

> *"The engineer who ships, measures, and fixes beats the engineer who only reads."*

---

## What this project builds (Step 1)

In this first step, we establish the project structure and configure the settings loading layer:
1. **Declarative Settings (`config.py`)** — Uses Pydantic Settings to search for system environment variables, load key-value pairs from a local `.env` configuration file, and perform type parsing.

No embedding connections, indexing logic, or plotting modules are initialized yet.

---

## Concepts Built So Far

### 1. Declarative Settings Validation
Instead of pulling environment configurations directly using typeless `os.environ` lookups, we define a structured schema class (`Settings`) inheriting from `BaseSettings`. This ensures:
* **Automated Type Casting** — Type signatures defined in Python (e.g. `int` ports) are automatically parsed from string representation.
* **Namespace Protection (`extra="ignore"`)** — Ignores any extra, unrecognized variables present on the host environment to prevent validation crashes.
* **Central Singleton** — Centralizes parsing into a single loaded instance (`settings`) accessed globally.

---

## How to install & run

### 1. Environment Setup
Create and activate your virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
Install the required settings validator:
```bash
pip install pydantic-settings
```

### 3. Verify Configuration Loading
Run a python snippet to verify settings initialization:
```python
from config import settings
print("Ollama URL:", settings.ollama_url)
print("Model Name:", settings.embed_model)
```

##### Expected Output:
```text
Ollama URL: http://127.0.0.1:11434
Model Name: nomic-embed-text
```

---

## Project structure

```
is02p02-mrl-benchmarker/
  config.py    Central settings loader singleton
```

---

## License

MIT © [Sachin Kolige](https://github.com/sachinks)
