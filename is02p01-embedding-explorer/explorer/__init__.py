"""Embedding Explorer - semantic vector tools built step by step."""

from .math_utils import dot_product, l2_norm, cosine_similarity
from .store import VectorStore
from .main import EmbeddingExplorer
from .visualise import visualise

__all__ = [
    "dot_product",
    "l2_norm",
    "cosine_similarity",
    "VectorStore",
    "EmbeddingExplorer",
    "visualise",
]


