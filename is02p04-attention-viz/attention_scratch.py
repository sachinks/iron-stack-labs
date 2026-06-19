import torch
import torch.nn.functional as F
import math

def attention(Q: torch.Tensor, K: torch.Tensor, V: torch.Tensor, mask: torch.Tensor = None):
    """
    Computes Scaled Dot-Product Attention.
    
    Args:
        Q: Queries of shape (batch, heads, seq_len, d_k)
        K: Keys of shape (batch, heads, seq_len, d_k)
        V: Values of shape (batch, heads, seq_len, d_v)
        mask: Optional binary mask of shape (seq_len, seq_len) or broadcastable.
              Positions with 0 (or False) will be filled with -1e9.
              
    Returns:
        output: Context-aware representation of shape (batch, heads, seq_len, d_v)
        weights: Attention weight distribution of shape (batch, heads, seq_len, seq_len)
    """
    d_k = Q.size(-1)
    
    # Step 1: Compute raw dot products scaled by sqrt(d_k)
    # Shape: (batch, heads, seq_len, seq_len)
    scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)
    
    # Step 2: Apply causal or custom mask if provided
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)
        
    # Step 3: Normalise scores to probability distribution
    weights = F.softmax(scores, dim=-1)
    
    # Step 4: Aggregate values weighted by attention distribution
    # Shape: (batch, heads, seq_len, d_v)
    output = torch.matmul(weights, V)
    
    return output, weights

def run_self_tests():
    print("--- Running Scaled Dot-Product Attention Self-Tests ---")
    
    # Setup dimensions
    batch = 2
    heads = 4
    seq_len = 5
    d_k = 64
    d_v = 64
    
    # Generate random tensors
    Q = torch.randn(batch, heads, seq_len, d_k)
    K = torch.randn(batch, heads, seq_len, d_k)
    V = torch.randn(batch, heads, seq_len, d_v)
    
    # Test 1: Unmasked Attention
    out, weights = attention(Q, K, V)
    assert out.shape == (batch, heads, seq_len, d_v), f"Expected output shape {(batch, heads, seq_len, d_v)}, got {out.shape}"
    assert weights.shape == (batch, heads, seq_len, seq_len), f"Expected weights shape {(batch, heads, seq_len, seq_len)}, got {weights.shape}"
    # Verify softmax sums to 1.0 along sequence length
    assert torch.allclose(weights.sum(dim=-1), torch.ones(batch, heads, seq_len)), "Softmax weights do not sum to 1.0"
    print("✓ Test 1: Unmasked Attention shapes and softmax normalization checked successfully.")
    
    # Test 2: Causal Masked Attention
    # Upper triangular mask (0s in upper triangle indicate future tokens)
    mask = torch.tril(torch.ones(seq_len, seq_len))
    out_masked, weights_masked = attention(Q, K, V, mask=mask)
    
    # Verify future positions have exactly 0 attention weights
    for i in range(seq_len):
        for j in range(i + 1, seq_len):
            assert torch.all(weights_masked[:, :, i, j] == 0.0), f"Future token {j} attended by token {i} under causal mask"
            
    print("✓ Test 2: Causal Mask masking checked successfully.")
    print("--- All Self-Tests Passed! ---")

if __name__ == "__main__":
    run_self_tests()
