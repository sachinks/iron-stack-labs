# context_placement.py — interleaving context chunks for optimal retrieval
from typing import List, Dict, Any

def place_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts and interleaves retrieved chunks to position the highest-scoring
    chunks at the start and end of the context window.
    
    Args:
        chunks: List of dictionaries containing "text" and "score" keys.
        
    Returns:
        reordered_chunks: Optimised list of chunks.
    """
    if len(chunks) <= 2:
        return chunks  # Already at boundaries
        
    # Step 1: Sort chunks descending by score
    sorted_chunks = sorted(chunks, key=lambda c: c.get("score", 0.0), reverse=True)
    
    # Step 2: Interleave them into front and back lists
    front = []
    back = []
    
    for i, chunk in enumerate(sorted_chunks):
        if i % 2 == 0:
            # Even rank (0, 2, 4...) goes to the front (highest first)
            front.append(chunk)
        else:
            # Odd rank (1, 3, 5...) goes to the back (reverse order)
            # By inserting at position 0, the higher rank goes to the outer end
            back.insert(0, chunk)
            
    # Step 3: Combine front and back lists
    return front + back

def run_tests():
    print("--- Running Context Placement Interleaving Tests ---")
    
    # Mock retrieved chunks with distinct scores
    mock_chunks = [
        {"id": "Doc A", "score": 0.95, "text": "Critical context details... (Rank 1)"},
        {"id": "Doc B", "score": 0.88, "text": "Supporting details... (Rank 2)"},
        {"id": "Doc C", "score": 0.72, "text": "Context filler text... (Rank 3)"},
        {"id": "Doc D", "score": 0.65, "text": "Vague relevant data... (Rank 4)"},
        {"id": "Doc E", "score": 0.50, "text": "Least relevant filler... (Rank 5)"},
    ]
    
    reordered = place_chunks(mock_chunks)
    
    # Let's inspect the results
    print("\nOriginal Order (by score descending):")
    for idx, c in enumerate(mock_chunks):
        print(f"  Rank {idx+1}: {c['id']} (Score: {c['score']})")
        
    print("\nReordered Interleaved Order:")
    for idx, c in enumerate(reordered):
        print(f"  Pos {idx+1}: {c['id']} (Score: {c['score']})")
        
    # Verify expected ordering
    # Rank 1 (0.95) should be at index 0 (first)
    # Rank 2 (0.88) should be at index -1 (last)
    # Rank 3 (0.72) should be at index 1 (second)
    # Rank 4 (0.65) should be at index -2 (second-to-last)
    # Rank 5 (0.50) should be in the middle (index 2)
    assert reordered[0]["id"] == "Doc A", "Expected Rank 1 at the beginning"
    assert reordered[-1]["id"] == "Doc B", "Expected Rank 2 at the end"
    assert reordered[1]["id"] == "Doc C", "Expected Rank 3 at position 2"
    assert reordered[-2]["id"] == "Doc D", "Expected Rank 4 at second-to-last position"
    assert reordered[2]["id"] == "Doc E", "Expected Rank 5 in the middle"
    
    print("\n✓ Context placement verification assertions passed successfully.")
    print("--- All Tests Passed! ---")

if __name__ == "__main__":
    run_tests()
