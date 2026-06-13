# main.py
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from config import settings
from logger import logger

app = FastAPI(title="Iron Stack — Concurrency Tester")

@app.get("/fake")
async def fake():
    try:
        logger.info("Fake async sleep endpoint called")
        await asyncio.sleep(2)
        response_data = {"response": "fake"}
        logger.debug(f"Fake sleep success: {response_data}")
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        logger.error(f"Error in fake endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
