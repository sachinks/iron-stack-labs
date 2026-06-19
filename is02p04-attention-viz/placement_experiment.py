# placement_experiment.py — measure lost-in-the-middle effect
import httpx
import asyncio
import sys

NEEDLE = "The capital of the Iron Stack project is Bengaluru."
QUESTION = "What is the capital of the Iron Stack project?"
# 130 repetitions of filler generates ~4000 characters (approx. 1000 tokens)
FILLER = ("The sky is blue. Water is wet. " * 130)

def build_context(position: str) -> str:
    """Places the needle at start, middle, or end of the filler context."""
    half = len(FILLER) // 2
    if position == "start":
        return f"{NEEDLE}\n\n{FILLER}"
    elif position == "end":
        return f"{FILLER}\n\n{NEEDLE}"
    else:  # middle
        # Split filler in half and insert the needle
        return f"{FILLER[:half]}\n\n{NEEDLE}\n\n{FILLER[half:]}"

async def ask_llm(client: httpx.AsyncClient, context: str, question: str) -> str:
    """Queries local Ollama instance with the compiled context and question."""
    url = "http://localhost:11434/v1/chat/completions"
    payload = {
        "model": "llama3.2",
        "messages": [
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}\nAnswer in one or two words only."
            }
        ],
        "temperature": 0.0  # Zero temperature for deterministic responses
    }
    try:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error querying Ollama: {e}", file=sys.stderr)
        return ""

async def evaluate_position(client: httpx.AsyncClient, position: str, num_trials: int = 10) -> float:
    """Runs multiple trials for a single position and reports accuracy."""
    print(f"Testing position: {position:<6} (Running {num_trials} trials)...")
    correct = 0
    context = build_context(position)
    
    # Run trials sequentially to avoid overloading the local CPU Ollama instance
    for trial in range(num_trials):
        ans = await ask_llm(client, context, QUESTION)
        hit = "bengaluru" in ans.lower() or "bangalore" in ans.lower()
        if hit:
            correct += 1
        print(f"  Trial {trial+1:2d}: Response: {ans.strip():<20} -> {'✓ HIT' if hit else '✗ MISS'}")
        
    accuracy = correct / num_trials
    return accuracy

async def main():
    print("--- Running Lost-in-the-Middle Empirical Experiment ---")
    
    # Validate Ollama availability first
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            test_resp = await client.get("http://localhost:11434/api/tags")
            test_resp.raise_for_status()
        except Exception:
            print("ERROR: Ollama server is not running at http://localhost:11434.", file=sys.stderr)
            print("Please make sure ollama is started ('ollama serve') before running this script.", file=sys.stderr)
            return

        results = {}
        positions = ["start", "middle", "end"]
        
        for pos in positions:
            accuracy = await evaluate_position(client, pos, num_trials=10)
            results[pos] = accuracy
            print(f"-> Accuracy for {pos}: {accuracy:.0%}\n")
            
        print("==========================================")
        print("SUMMARY RESULTS")
        print("==========================================")
        for pos in positions:
            print(f"Position: {pos:<6} | Accuracy: {results[pos]:.0%}")
        
        degradation = results["start"] - results["middle"]
        print(f"Middle Position Degradation: {degradation:.0%}")
        print("==========================================")

if __name__ == "__main__":
    asyncio.run(main())
