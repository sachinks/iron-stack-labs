# main.py
"""Main application entry point for the Local LLM Gateway."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from config import settings
from logger import logger

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
