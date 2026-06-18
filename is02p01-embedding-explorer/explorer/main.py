"""explorer/main.py - Controller bridging embedding model and vector store.

This module provides the central coordinator class EmbeddingExplorer that handles
text encoding via sentence-transformers and inserts them into our VectorStore.
"""

from sentence_transformers import SentenceTransformer
from .store import VectorStore
from .visualise import visualise


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

    def add(self, text: str) -> list[float]:
        """Generate embedding for text and add to the vector store.

        Args:
            text: The text string to embed and store.

        Returns:
            The generated embedding vector as a list of floats.
        """
        embedding = self.encode(text)
        # Ensure it is a list of floats, not list of lists
        assert isinstance(embedding, list) and isinstance(embedding[0], float)
        self.store.add(text, embedding)
        return embedding

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Encode query string and search the store."""
        query_embedding = self.encode(query)
        assert isinstance(query_embedding, list) and isinstance(query_embedding[0], float)
        return self.store.search(query_embedding, top_k=top_k)


CORPUS = [
    # Programming
    ("Python is a high-level programming language.", "programming"),
    ("I love writing code and building software.", "programming"),
    ("Async functions in Python return coroutines.", "programming"),
    ("Debugging is the art of removing software bugs.", "programming"),
    ("Git tracks changes across versions of source code.", "programming"),
    # Animals (incl. the python-snake polysemy collision)
    ("A python is a large snake that squeezes its prey.", "animals"),
    ("Cats are wonderful pets that sleep all day.", "animals"),
    ("Dogs are loyal companions and love to play fetch.", "animals"),
    ("Eagles soar high above the mountains hunting prey.", "animals"),
    # Cooking
    ("Searing meat creates a rich brown crust.", "cooking"),
    ("Sous vide cooks food slowly in a warm water bath.", "cooking"),
    ("Fresh basil and garlic make a fragrant pesto.", "cooking"),
    ("Knead the dough until it becomes smooth and elastic.", "cooking"),
    # Finance
    ("The stock market crashed sharply today.", "finance"),
    ("Interest rates affect the cost of borrowing money.", "finance"),
    ("Investors diversify portfolios to reduce risk.", "finance"),
    ("Inflation erodes the purchasing power of savings.", "finance"),
    # Sports
    ("The cricket team won the match in the final over.", "sports"),
    ("She scored a stunning goal in the last minute.", "sports"),
    ("Marathon runners train for months before the race.", "sports"),
    # Weather / nature
    ("Heavy monsoon rains flooded the coastal city.", "weather"),
    ("A gentle breeze cooled the warm summer evening.", "weather"),
    ("Thunderstorms are common during the afternoon heat.", "weather"),
    ("Snow blanketed the quiet village overnight.", "weather"),
]


if __name__ == "__main__":
    print("=== Testing EmbeddingExplorer ===")
    
    explorer = EmbeddingExplorer()
    
    texts = [t for t, _ in CORPUS]
    groups = [g for _, g in CORPUS]
    
    print("Encoding and adding corpus...")
    for text in texts:
        explorer.add(text)
        
    print(f"Store loaded with {len(explorer.store)} items.")
    
    # Query Topic A
    query_a = "I enjoy programming in python"
    print(f"\nQuerying: '{query_a}'")
    for r in explorer.search(query_a, top_k=3):
        print(f"  Rank {r['rank']}: Score {r['score']:.4f} -> {r['text']}")
        
    # Query Topic B
    query_b = "dangerous pythons and snakes"
    print(f"\nQuerying: '{query_b}'")
    for r in explorer.search(query_b, top_k=3):
        print(f"  Rank {r['rank']}: Score {r['score']:.4f} -> {r['text']}")
        
    print("\nGenerating UMAP visualization...")
    visualise(explorer.store, output_path="embedding_space.png", groups=groups)
    
    print("=== Checks complete ===")
