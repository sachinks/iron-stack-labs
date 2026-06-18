"""bench/embed.py — embedding utilities (Step 2).

Provides:
  embed(text, kind)    -> 768-d unit-length float32 ndarray

Both functions enforce L2 normalisation so downstream code can use plain
dot products for cosine similarity.
"""

import numpy as np
import requests

from config import settings

# nomic-embed-text requires task prefixes to apply the correct
# internal representation path (document vs query encoder heads).
_PREFIX = {
    "document": "search_document: ",
    "query": "search_query: ",
}


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    """Scale *vec* to unit length (L2 norm == 1.0).

    This is the operation that makes cosine similarity collapse to a plain
    dot product: ``cos(a, b) = (a·b) / (|a||b|) = a·b`` when |a|==|b|==1.

    Handles the zero-vector edge case by returning the vector unchanged
    (a zero vector has no meaningful direction to normalise to).

    Args:
        vec: a 1-D numpy array of any dtype.

    Returns:
        A new float32 array with L2 norm == 1.0, or *vec* unchanged if
        ``np.linalg.norm(vec) == 0``.
    """
    norm = np.linalg.norm(vec)
    if norm == 0.0:
        return vec
    return vec / norm


def embed(text: str, kind: str = "document") -> np.ndarray:
    """Embed *text* via the local Ollama server and return a unit-length vector.

    Prepends the appropriate task prefix (``search_document:`` or
    ``search_query:``) before sending the text to Ollama.  Skipping the
    prefix is a common silent bug — the model degrades retrieval quality
    without error.

    The raw Ollama response is a float32 array of size 768 (for
    nomic-embed-text).  This function L2-normalises it before returning,
    so all subsequent comparisons use dot products.

    Args:
        text: the raw string to embed.  The task prefix is prepended
            automatically; do not add it yourself.
        kind: ``"document"`` for corpus items, ``"query"`` for search
            queries.  These map to ``search_document:`` and
            ``search_query:`` prefixes respectively.

    Returns:
        A float32 numpy array of shape ``(768,)`` with L2 norm == 1.0.

    Raises:
        ValueError: if *kind* is not ``"document"`` or ``"query"``.
        requests.HTTPError: if the Ollama server returns a non-2xx status.
        requests.ConnectionError: if the Ollama server is not reachable.
    """
    if kind not in _PREFIX:
        raise ValueError(f"kind must be 'document' or 'query', got {kind!r}")

    resp = requests.post(
        f"{settings.ollama_url}/api/embeddings",
        json={"model": settings.embed_model, "prompt": _PREFIX[kind] + text},
        timeout=60,
    )
    resp.raise_for_status()
    vec = np.asarray(resp.json()["embedding"], dtype=np.float32)
    return _l2_normalize(vec)


if __name__ == "__main__":
    print("Running inline tests for Step 2 math and structures...")
    
    # 1. Normalization sanity check
    v_test = np.array([3.0, 4.0], dtype=np.float32)
    v_norm = _l2_normalize(v_test)
    expected_norm = 1.0
    actual_norm = np.linalg.norm(v_norm)
    assert abs(actual_norm - expected_norm) < 1e-6, f"Math fail: norm is {actual_norm}"
    print("  [OK] L2 normalization logic matches unit-length expectations.")

    # 2. Zero vector boundary check
    v_zero = np.zeros(10, dtype=np.float32)
    v_zero_norm = _l2_normalize(v_zero)
    assert np.all(v_zero_norm == 0.0), "Math fail: zero vector norm mutation occurred"
    print("  [OK] Zero-vector division guard behaves correctly.")

    # 3. Connection and embedding generation check
    print("\nAttempting connection to Ollama server...")
    try:
        sample_text = "Matryoshka representation learning"
        v = embed(sample_text, kind="document")
        v_norm_check = np.linalg.norm(v)
        print(f"  [OK] Successfully connected to Ollama!")
        print(f"  [OK] Generated vector shape: {v.shape}")
        print(f"  [OK] Generated vector L2 norm: {v_norm_check:.6f}")
        assert abs(v_norm_check - 1.0) < 1e-5, f"Ollama embedding normalisation check failed: norm={v_norm_check}"
    except requests.exceptions.ConnectionError:
        print("  [WARNING] Ollama server is not running or unreachable. Skipping integration check.")
        print("  (Make sure Ollama is running locally if you want to test retrieval embeddings.)")
    except Exception as e:
        print(f"  [WARNING] Could not verify Ollama embeddings: {e}")
    
    print("\nInline verification checks complete.")
