# handlers/async_handler.py
import time
import httpx
from fastapi import APIRouter, Request, HTTPException
from config import settings
from logger import logger

router = APIRouter()

@router.post("/async/chat")
async def async_chat(prompt: str, request: Request) -> dict:
    try:
        logger.info(f"Async chat request received. Prompt length: {len(prompt)}")
        client: httpx.AsyncClient = request.app.state.client
        start = time.perf_counter()
        
        response = await client.post(
            f"{settings.openai_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.model_name,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        
        latency = (time.perf_counter() - start) * 1000
        content = response.json()["choices"][0]["message"]["content"]
        
        logger.info(f"Async chat completed in {latency:.1f}ms")
        return {
            "response": content,
            "latency_ms": round(latency, 1),
            "handler": "async",
        }
    except Exception as e:
        logger.error(f"Error in async_chat handler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Async request failed: {str(e)}")
