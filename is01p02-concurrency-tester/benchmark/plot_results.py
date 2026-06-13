# benchmark/plot_results.py
import asyncio
import time
import statistics
import httpx
import sys
import logging
from config import settings

# Configure logging
logger = logging.getLogger("plot_results")
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
        logger.error(f"Query failure to {url}: {e}")
        return 0.0

async def run_scenario(client: httpx.AsyncClient, url: str, label: str, concurrent: bool, method: str = "GET", params: dict = None) -> dict:
    try:
        logger.info(f"Benchmarking scenario: {label}")
        if concurrent:
            tasks = [fetch(client, url, method, params) for _ in range(settings.concurrent_users)]
            times = list(await asyncio.gather(*tasks))
        else:
            times = []
            for _ in range(settings.concurrent_users):
                t = await fetch(client, url, method, params)
                times.append(t)
        
        valid_times = [t for t in times if t > 0.0]
        if not valid_times:
            return {"p50": 0.0, "p95": 0.0}
            
        p50 = statistics.median(valid_times)
        p95 = statistics.quantiles(valid_times, n=20)[18] if len(valid_times) >= 20 else max(valid_times)
        return {"p50": p50, "p95": p95}
    except Exception as e:
        logger.error(f"Error running scenario {label}: {e}")
        return {"p50": 0.0, "p95": 0.0}

async def generate_chart():
    try:
        logger.info("Starting programmatic benchmark runs for visualization")
        ollama_params = {"prompt": settings.test_prompt}
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            fake_sync = await run_scenario(client, f"{BASE_URL}/fake", "SYNC FAKE", concurrent=False)
            fake_async = await run_scenario(client, f"{BASE_URL}/fake", "ASYNC FAKE", concurrent=True)
            ollama_sync = await run_scenario(client, f"{BASE_URL}/sync/chat", "SYNC OLLAMA", concurrent=True, method="POST", params=ollama_params)
            ollama_async = await run_scenario(client, f"{BASE_URL}/async/chat", "ASYNC OLLAMA", concurrent=True, method="POST", params=ollama_params)
            
        # Draw chart using Matplotlib
        import matplotlib.pyplot as plt
        import numpy as np
        
        logger.info("Plotting benchmark latency results using Matplotlib")
        scenarios = ["Fake (Sync)", "Fake (Async)", "Ollama (Sync)", "Ollama (Async)"]
        p50_values = [fake_sync["p50"], fake_async["p50"], ollama_sync["p50"], ollama_async["p50"]]
        p95_values = [fake_sync["p95"], fake_async["p95"], ollama_sync["p95"], ollama_async["p95"]]
        
        x = np.arange(len(scenarios))
        width = 0.35
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
        
        # Premium color definitions (Harmonious blues/purples)
        p50_color = '#3b82f6'  # Accent Blue
        p95_color = '#8b5cf6'  # Accent Purple
        
        rects1 = ax.bar(x - width/2, p50_values, width, label='P50 (Median)', color=p50_color, edgecolor='rgba(255,255,255,0.1)')
        rects2 = ax.bar(x + width/2, p95_values, width, label='P95 (Tail)', color=p95_color, edgecolor='rgba(255,255,255,0.1)')
        
        ax.set_ylabel('Latency (Seconds)', fontsize=12, color='#94a3b8')
        ax.set_title(f'Latency Comparison under Concurrency ({settings.concurrent_users} Users)', fontsize=14, fontweight='bold', pad=20, color='#f8fafc')
        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, fontsize=10, color='#94a3b8')
        ax.legend(frameon=True, facecolor='#1e293b', edgecolor='none')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#334155')
        ax.spines['bottom'].set_color('#334155')
        ax.grid(axis='y', linestyle='--', alpha=0.2)
        
        # Add labels on bars
        def autolabel(rects):
            for rect in rects:
                height = rect.get_height()
                if height > 0.0:
                    ax.annotate(f'{height:.2f}s',
                                xy=(rect.get_x() + rect.get_width() / 2, height),
                                xytext=(0, 3),  # 3 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom', fontsize=8, color='#f1f5f9')
                            
        autolabel(rects1)
        autolabel(rects2)
        
        fig.tight_layout()
        output_path = "benchmark/latency_comparison.png"
        plt.savefig(output_path, facecolor='#0f172a', bbox_inches='tight')
        plt.close()
        logger.info(f"Latency visualization saved successfully to {output_path}")
        
    except ImportError:
        logger.warning("Matplotlib is not installed in the current environment; skipping graphical generation.")
    except Exception as e:
        logger.error(f"Error rendering benchmark graph: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(generate_chart())
