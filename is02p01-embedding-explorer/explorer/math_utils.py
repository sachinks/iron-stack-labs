"""Pure Python vector math for cosine similarity.

Step 1 builds the geometry layer before any ML library: dot product, L2 norm,
and cosine similarity using only the standard library.
"""

import math


def dot_product(u: list[float], v: list[float]) -> float:
    """Return the dot product of two equal-length vectors.

    Args:
        u: First vector.
        v: Second vector.

    Returns:
        Scalar dot product sum(u_i * v_i).

    Raises:
        ValueError: If either vector is empty or lengths differ.
    """
    if not u or not v:
        raise ValueError("Vectors must not be empty.")
    if len(u) != len(v):
        raise ValueError("Vectors must have the same length.")
    return sum(ui * vi for ui, vi in zip(u, v))


def l2_norm(u: list[float]) -> float:
    """Return the L2 (Euclidean) norm of a vector.

    Args:
        u: Input vector.

    Returns:
        sqrt(sum(u_i ** 2)).

    Raises:
        ValueError: If the vector is empty.
    """
    if not u:
        raise ValueError("Vector must not be empty.")
    return math.sqrt(sum(ui * ui for ui in u))


def cosine_similarity(u: list[float], v: list[float]) -> float:
    """Return cosine similarity cos(theta) between two vectors.

    Measures directional alignment only; magnitude is normalised out.
    Result is in [-1.0, 1.0] for non-zero inputs.

    Args:
        u: First vector.
        v: Second vector.

    Returns:
        dot(u, v) / (||u|| * ||v||).

    Raises:
        ValueError: If vectors are empty, lengths differ, or either has zero norm.
    """
    norm_u = l2_norm(u)
    norm_v = l2_norm(v)
    if norm_u == 0.0 or norm_v == 0.0:
        raise ValueError(
            "Cannot compute cosine similarity with a zero vector (L2 norm is 0.0)."
        )
    return dot_product(u, v) / (norm_u * norm_v)


if __name__ == "__main__":
    print("=== IS02P01 Step 1 - math_utils sanity checks ===")

    identical = [1.0, 2.0, 3.0]
    score = cosine_similarity(identical, [1.0, 2.0, 3.0])
    print(f"Identical vectors:        {score:.4f}  (expected 1.0000)")

    orthogonal = cosine_similarity([1.0, 0.0], [0.0, 1.0])
    print(f"Orthogonal vectors:       {orthogonal:.4f}  (expected 0.0000)")

    opposite = cosine_similarity([1.0, -1.0], [-1.0, 1.0])
    print(f"Opposite vectors:         {opposite:.4f}  (expected -1.0000)")

    try:
        dot_product([], [1.0])
    except ValueError as exc:
        print(f"Empty vector guard:       {exc}")

    try:
        dot_product([1.0, 2.0], [1.0])
    except ValueError as exc:
        print(f"Length mismatch guard:  {exc}")

    try:
        cosine_similarity([0.0, 0.0], [1.0, 2.0])
    except ValueError as exc:
        print(f"Zero-vector guard:        {exc}")

    print("=== All checks complete ===")
