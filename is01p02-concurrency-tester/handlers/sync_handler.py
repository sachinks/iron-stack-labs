# handlers/sync_handler.py
import requests
import time
from fastapi import APIRouter, HTTPException
from config import settings
from logger import logger

router = APIRouter()

@router.post("/sync/chat")
def sync_chat(prompt: str) -> dict:
    try:
        logger.info(f"Sync chat request received. Prompt length: {len(prompt)}")
        start = time.perf_counter()
        
        response = requests.post(
            f"{settings.openai_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.model_name,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        response.raise_for_status()
        
        latency = (time.perf_counter() - start) * 1000
        content = response.json()["choices"][0]["message"]["content"]
        
        logger.info(f"Sync chat completed in {latency:.1f}ms")
        return {
            "response": content,
            "latency_ms": round(latency, 1),
            "handler": "sync",
        }
    except Exception as e:
        logger.error(f"Error in sync_chat handler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync request failed: {str(e)}")
