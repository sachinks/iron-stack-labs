# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from config import settings
from logger import logger
from redis_client import redis_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Verifying connection to Redis service pool...")
        # Ping Redis to verify connection pool works
        await redis_client.ping()
        logger.info("Successfully connected to Redis instance.")
        yield
    except Exception as e:
        logger.error(f"Failed to establish connection to Redis at startup: {e}", exc_info=True)
        raise e
    finally:
        try:
            logger.info("Closing Redis connection pool...")
            await redis_client.close()
            logger.info("Redis connection pool closed successfully.")
        except Exception as close_e:
            logger.error(f"Error closing Redis connection pool: {close_e}", exc_info=True)

app = FastAPI(lifespan=lifespan, title="Iron Stack — Multitenant API")

@app.get("/health")
async def health():
    try:
        logger.info("Health check endpoint called")
        response_data = {"status": "healthy"}
        logger.debug(f"Health check status: {response_data}")
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
