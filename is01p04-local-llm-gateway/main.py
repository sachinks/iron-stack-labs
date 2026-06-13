# main.py
"""Main application entry point for the Local LLM Gateway."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from config import settings
from logger import logger
from gateway.llm_client import get_llm_client

app = FastAPI(title="Iron Stack — Local LLM Gateway")

@app.get("/health")
async def health():
    """Simple health check endpoint."""
    try:
        logger.info("Health check endpoint called")
        response_data = {"status": "ok"}
        logger.debug(f"Health check status: {response_data}")
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/chat")
async def chat(request: Request):
    """Mock chat completions route."""
    try:
        logger.info("Mock chat completions endpoint called")
        body = await request.json()
        prompt = body.get("prompt", "")
        logger.debug(f"Received prompt: {prompt}")
        
        # Instantiate client to verify connectivity/configuration works
        _ = get_llm_client()
        
        response_data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": f"Mock response to: {prompt}"
                    }
                }
            ]
        }
        logger.debug("Mock chat response successfully created")
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        logger.error(f"Error in mock chat completions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
