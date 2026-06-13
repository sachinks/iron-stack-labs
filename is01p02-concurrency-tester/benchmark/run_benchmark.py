# benchmark/run_benchmark.py
import asyncio
import time
import statistics
import httpx
import sys
import logging
from config import settings

logger = logging.getLogger("benchmark")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
    logger.addHandler(handler)

BASE_URL = "http://localhost:8000"

async def fetch(client: httpx.AsyncClient, url: str, method: str = "GET", params: dict = None) -> float:
    try:
        start = time.time()
        if method == "GET":
            await client.get(url)
        else:
            await client.post(url, params=params)
        end = time.time()
        return end - start
    except Exception as e:
        logger.error(f"Failed query to {url}: {e}")
        return 0.0

async def run_benchmark(
        url: str, label: str, concurrent: bool = True, method: str = "GET", params: dict = None) -> list[float]:
    try:
        logger.info(f"Starting benchmark for {label}")
        async with httpx.AsyncClient(timeout=300.0) as client:
            wall_start = time.time()
            if concurrent:
                tasks = [fetch(client, url, method, params) for _ in range(settings.concurrent_users)]
                times = list(await asyncio.gather(*tasks))
            else:
                times = []
                for _ in range(settings.concurrent_users):
                    t = await fetch(client, url, method, params)
                    times.append(t)
            wall_end = time.time()
            wall_time = wall_end - wall_start

        valid_times = [t for t in times if t > 0.0]
        if not valid_times:
            logger.warning(f"No successful queries completed for {label}")
            return []

        p50 = statistics.median(valid_times)
        p95 = statistics.quantiles(valid_times, n=20)[18] if len(valid_times) >= 20 else max(valid_times)

        print(f"\n{label} BENCHMARK ({len(valid_times)} requests)")
        print(f"  P50 (median):  {p50:.3f}s")
        print(f"  P95:           {p95:.3f}s")
        print(f"  Total time:    {sum(valid_times):.3f}s")
        print(f"  Wall time:     {wall_time:.3f}s")
        return valid_times
    except Exception as e:
        logger.error(f"Error executing benchmark {label}: {e}", exc_info=True)
        return []

async def main():
    try:
        ollama_params = {"prompt": settings.test_prompt}

        print("--- FAKE ENDPOINT (proves async) ---")
        await run_benchmark(f"{BASE_URL}/fake", "SYNC FAKE", concurrent=False)
        await run_benchmark(f"{BASE_URL}/fake", "ASYNC FAKE", concurrent=True)

        print("\n--- REAL OLLAMA (for reference) ---")
        await run_benchmark(f"{BASE_URL}/sync/chat", 
                            "SYNC OLLAMA", concurrent=True, method="POST", params=ollama_params)
        await run_benchmark(f"{BASE_URL}/async/chat", 
                            "ASYNC OLLAMA", concurrent=True, method="POST", params=ollama_params)
    except Exception as e:
        logger.error(f"Error in benchmark main: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
