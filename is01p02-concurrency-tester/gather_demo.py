# gather_demo.py
import asyncio
import httpx
import time
import sys
import logging
from config import settings

logger = logging.getLogger("gather_demo")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
    logger.addHandler(handler)

async def call_llm(client: httpx.AsyncClient, prompt: str) -> str:
    try:
        logger.info(f"Dispatching query to LLM: '{prompt}'")
        r = await client.post(
            f"{settings.openai_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.model_name,
                "messages": [{"role": "user", "content": prompt}]
            },
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        logger.info("Successfully received LLM response")
        return content
    except Exception as e:
        logger.error(f"Failed to query LLM for prompt '{prompt}': {e}", exc_info=True)
        raise e

async def sequential_calls(prompts: list[str]) -> list[str]:
    try:
        logger.info("Starting sequential execution of LLM requests")
        async with httpx.AsyncClient(timeout=60.0) as client:
            results = []
            for prompt in prompts:
                results.append(await call_llm(client, prompt))
            return results
    except Exception as e:
        logger.error(f"Sequential requests execution failed: {e}", exc_info=True)
        raise e

async def parallel_calls(prompts: list[str]) -> list[str]:
    try:
        logger.info("Starting concurrent execution of LLM requests using asyncio.gather")
        async with httpx.AsyncClient(timeout=60.0) as client:
            return await asyncio.gather(
                *[call_llm(client, p) for p in prompts]
            )
    except Exception as e:
        logger.error(f"Concurrent requests execution failed: {e}", exc_info=True)
        raise e

async def main():
    try:
        logger.info("Bootstrapping gather concurrency comparison")
        prompts = [f"Reply in one word only. What is number {i}?" for i in range(5)]

        t0 = time.perf_counter()
        await sequential_calls(prompts)
        seq_time = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        await parallel_calls(prompts)
        par_time = (time.perf_counter() - t0) * 1000

        print(f"\nSequential 5 calls: {seq_time:.0f}ms")
        print(f"Parallel   5 calls: {par_time:.0f}ms")
        speedup = seq_time / par_time if par_time > 0 else 0
        print(f"Speedup: {speedup:.1f}x\n")
    except Exception as e:
        logger.error(f"Error in gather_demo main loop: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Failed to run gather_demo: {e}")
