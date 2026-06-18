"""explorer/store.py - In-memory vector store utilizing pure Python similarity math.

This module provides a basic container for (text, embedding) pairs. It uses the
pure Python cosine similarity math from explorer.math_utils for educational purposes.
"""

from .math_utils import cosine_similarity


class VectorStore:
    """In-memory vector store for text and float vector pairs."""

    def __init__(self) -> None:
        """Initialize an empty vector store."""
        self._texts: list[str] = []
        self._embeddings: list[list[float]] = []

    def add(self, text: str, embedding: list[float]) -> None:
        """Add a text and embedding pair to the store.

        Args:
            text: The text string to associate with the vector.
            embedding: The embedding vector as a list of floats.

        Raises:
            ValueError: If the embedding is empty or its length does not match
                        existing vectors.
        """
        if not embedding:
            raise ValueError("Embedding must not be empty.")
        
        if self._embeddings:
            expected_dim = len(self._embeddings[0])
            if len(embedding) != expected_dim:
                raise ValueError(
                    f"Vector dimension mismatch. Expected dimension {expected_dim}, "
                    f"but got {len(embedding)}."
                )
        
        self._texts.append(text)
        self._embeddings.append(embedding)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Search the store for vectors closest to the query embedding.

        Args:
            query_embedding: The query vector as a list of floats.
            top_k: The maximum number of results to return.

        Returns:
            A list of ranked results:
            [
                {"rank": 1, "score": 0.85, "text": "matched text"},
                ...
            ]

        Raises:
            ValueError: If the query embedding is empty or has a length mismatch.
        """
        if not query_embedding:
            raise ValueError("Query embedding must not be empty.")
            
        if not self._embeddings:
            return []
            
        expected_dim = len(self._embeddings[0])
        if len(query_embedding) != expected_dim:
            raise ValueError(
                f"Query dimension mismatch. Expected dimension {expected_dim}, "
                f"but got {len(query_embedding)}."
            )
            
        # Compute cosine similarity for all vectors
        results = []
        for i, stored_vec in enumerate(self._embeddings):
            score = cosine_similarity(query_embedding, stored_vec)
            results.append((score, self._texts[i]))
            
        # Sort results by similarity score in descending order
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Take the top_k
        top_results = results[:top_k]
        
        return [
            {
                "rank": rank + 1,
                "score": round(score, 4),
                "text": text,
            }
            for rank, (score, text) in enumerate(top_results)
        ]

    def get_all(self) -> dict:
        """Return all stored texts and embeddings.

        Returns:
            A dict with keys "texts" and "embeddings".
        """
        return {
            "texts": self._texts,
            "embeddings": self._embeddings,
        }

    def __len__(self) -> int:
        """Return the number of items in the store."""
        return len(self._texts)


if __name__ == "__main__":
    print("=== Running sanity checks for VectorStore ===")
    
    store = VectorStore()
    
    # 1. Verify empty store returns empty search results
    print(f"Empty search results: {store.search([1.0, 0.0])} (Expected: [])")
    
    # 2. Add vectors
    store.add("Topic A: cats", [1.0, 0.0, 0.0])
    store.add("Topic B: dogs", [0.0, 1.0, 0.0])
    store.add("Topic A2: kittens", [0.8, 0.2, 0.0])
    
    print(f"Store size: {len(store)} (Expected: 3)")
    
    # 3. Perform a query close to Topic A
    query = [0.9, 0.1, 0.0]
    results = store.search(query, top_k=2)
    print("Search results for [0.9, 0.1, 0.0]:")
    for r in results:
        print(f"  Rank {r['rank']}: Score {r['score']:.4f} -> {r['text']}")
        
    # 4. Dimension mismatch exception when adding
    try:
        store.add("Invalid dimension", [1.0, 2.0])
    except ValueError as e:
        print(f"Caught expected dimension mismatch on add: '{e}'")
        
    # 5. Dimension mismatch exception when searching
    try:
        store.search([1.0, 2.0])
    except ValueError as e:
        print(f"Caught expected dimension mismatch on search: '{e}'")

    print("=== Checks complete ===")
