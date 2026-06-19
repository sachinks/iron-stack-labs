# kv_cache_calc.py — compute KV cache memory requirements
from dataclasses import dataclass

@dataclass
class ModelConfig:
    name: str
    num_layers: int
    num_heads: int
    head_dim: int
    dtype_bytes: int = 2  # float16/bfloat16 = 2, float32 = 4, int8 = 1

# Model configurations from literature/specs
MODELS = {
    "llama3.2-1b": ModelConfig("Llama 3.2 1B", 16, 8, 64),
    "llama3.2-3b": ModelConfig("Llama 3.2 3B", 28, 8, 128),
    "llama3.3-70b": ModelConfig("Llama 3.3 70B", 80, 64, 128),
    "llama3.1-405b": ModelConfig("Llama 3.1 405B", 126, 128, 128),
}

def kv_cache_gb(cfg: ModelConfig, seq_len: int) -> float:
    """
    Computes KV cache memory in gigabytes (GB).
    
    Formula:
    KV_cache_bytes = 2 * layers * heads * head_dim * seq_len * dtype_bytes
    """
    bytes_total = 2 * cfg.num_layers * cfg.num_heads * cfg.head_dim * seq_len * cfg.dtype_bytes
    return bytes_total / (1024 ** 3)

def print_report(model_key: str):
    cfg = MODELS[model_key]
    print(f"\n==========================================")
    print(f"{cfg.name}")
    print(f"==========================================")
    print(f"Layers:    {cfg.num_layers}")
    print(f"Heads:     {cfg.num_heads}")
    print(f"Head Dim:  {cfg.head_dim}")
    print(f"Precision: {cfg.dtype_bytes * 8}-bit ({cfg.dtype_bytes} bytes/param)")
    print(f"------------------------------------------")
    for ctx in [1024, 4096, 16384, 32768, 131072]:
        gb = kv_cache_gb(cfg, ctx)
        print(f" Context = {ctx:7d} tokens → KV Cache = {gb:.2f} GB")
    print(f"==========================================")

def main():
    print("--- Running KV Cache Memory Calculator ---")
    for model_key in MODELS:
        print_report(model_key)

if __name__ == "__main__":
    main()
