"""explorer/main.py - Controller bridging embedding model and vector store.

This module provides the central coordinator class EmbeddingExplorer that handles
text encoding via sentence-transformers and inserts them into our VectorStore.
"""

from sentence_transformers import SentenceTransformer
from .store import VectorStore


class EmbeddingExplorer:
    """Manages text encoding, storage, and semantic querying."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the embedding explorer with a model and store."""
        # Force CPU-only to prevent CUDA mount dependency issues in WSL
        self.model = SentenceTransformer(model_name, device="cpu")
        self.store = VectorStore()

    def encode(self, texts: str | list[str]) -> list[float] | list[list[float]]:
        """Encode text(s) into high-dimensional embeddings."""
        if isinstance(texts, str):
            # Convert NumPy array to standard Python float list
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        else:
            embeddings = self.model.encode(texts)
            return [emb.tolist() for emb in embeddings]

    def add(self, text: str) -> None:
        """Generate embedding for text and add to the vector store."""
        embedding = self.encode(text)
        # Ensure it is a list of floats, not list of lists
        assert isinstance(embedding, list) and isinstance(embedding[0], float)
        self.store.add(text, embedding)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Encode query string and search the store."""
        query_embedding = self.encode(query)
        assert isinstance(query_embedding, list) and isinstance(query_embedding[0], float)
        return self.store.search(query_embedding, top_k=top_k)


if __name__ == "__main__":
    print("=== Testing EmbeddingExplorer ===")
    
    explorer = EmbeddingExplorer()
    
    # Seeding with a simple 6-sentence corpus across 3 distinct topics
    corpus = [
        "The quick brown fox jumps over the lazy dog.",
        "A fast canine leaps across a sleepy pup.",          # Topic A: Animals leaping
        "Information flow architecture defines how data moves.",
        "Data pipelines route records between services.",   # Topic B: Software architecture
        "Quantum computing relies on qubits and superposition.",
        "Superconducting circuits enable quantum processors." # Topic C: Quantum computers
    ]
    
    print("Encoding and adding corpus...")
    for text in corpus:
        explorer.add(text)
        
    print(f"Store loaded with {len(explorer.store)} items.")
    
    # Query Topic A
    query_a = "Canines leaping over dogs"
    print(f"\nQuerying: '{query_a}'")
    for r in explorer.search(query_a, top_k=2):
        print(f"  Rank {r['rank']}: Score {r['score']:.4f} -> {r['text']}")
        
    # Query Topic B
    query_b = "System data routing pipelines"
    print(f"\nQuerying: '{query_b}'")
    for r in explorer.search(query_b, top_k=2):
        print(f"  Rank {r['rank']}: Score {r['score']:.4f} -> {r['text']}")
        
    print("=== Checks complete ===")
