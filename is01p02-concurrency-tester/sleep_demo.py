# sleep_demo.py
import asyncio
import time
import sys
import logging

# Configure basic console logger for standalone script execution
logger = logging.getLogger("sleep_demo")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s'))
    logger.addHandler(handler)

async def blocking_sleep():
    try:
        logger.info("Entering blocking_sleep (time.sleep)")
        start = time.perf_counter()
        time.sleep(1)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(f"Exiting blocking_sleep: took {duration_ms:.1f}ms")
        return duration_ms
    except Exception as e:
        logger.error(f"Error in blocking_sleep: {e}", exc_info=True)
        raise e

async def nonblocking_sleep():
    try:
        logger.info("Entering nonblocking_sleep (asyncio.sleep)")
        start = time.perf_counter()
        await asyncio.sleep(1)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(f"Exiting nonblocking_sleep: took {duration_ms:.1f}ms")
        return duration_ms
    except Exception as e:
        logger.error(f"Error in nonblocking_sleep: {e}", exc_info=True)
        raise e

async def run_10_concurrent(fn):
    try:
        logger.info(f"Starting execution of 10 concurrent requests using {fn.__name__}")
        start = time.perf_counter()
        await asyncio.gather(*[fn() for _ in range(10)])
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(f"Completed 10 concurrent requests: total execution took {duration_ms:.1f}ms")
        return duration_ms
    except Exception as e:
        logger.error(f"Error executing concurrent runs: {e}", exc_info=True)
        raise e

async def main():
    try:
        logger.info("Starting Concurrency Comparison Demo")
        
        nonblocking_ms = await run_10_concurrent(nonblocking_sleep)
        logger.info(f"10x asyncio.sleep(1) finished in: {nonblocking_ms:.0f}ms")

        blocking_ms = await run_10_concurrent(blocking_sleep)
        logger.info(f"10x time.sleep(1) finished in: {blocking_ms:.0f}ms")

        ratio = blocking_ms / nonblocking_ms if nonblocking_ms > 0 else 0
        logger.info(f"Ratio: {ratio:.1f}x slower with time.sleep")
    except Exception as e:
        logger.error(f"Failed in main execution loop: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as run_e:
        print(f"Failed to bootstrap script: {run_e}")
