# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from config import settings
from logger import logger

app = FastAPI(title="Iron Stack — LiveChat API")

@app.get("/health")
async def health():
    try:
        logger.info("Health check endpoint invoked")
        response_data = {"status": "healthy"}
        logger.debug(f"Health check succeeded, payload: {response_data}")
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        logger.error(f"Health check failed with error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
