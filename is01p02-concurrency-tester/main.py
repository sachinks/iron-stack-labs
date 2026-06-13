# main.py
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from handlers.sync_handler import router as sync_router
from handlers.async_handler import router as async_router
from handlers.fake_handler import router as fake_router
from logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Initializing persistent httpx.AsyncClient during startup")
        app.state.client = httpx.AsyncClient(timeout=120.0)
        yield
    except Exception as startup_e:
        logger.error(f"Lifespan startup failure: {startup_e}", exc_info=True)
        raise startup_e
    finally:
        try:
            logger.info("Closing persistent httpx.AsyncClient during shutdown")
            await app.state.client.aclose()
        except Exception as shutdown_e:
            logger.error(f"Lifespan shutdown error: {shutdown_e}", exc_info=True)

app = FastAPI(lifespan=lifespan, title="Iron Stack — Concurrency Tester")

# Include modular routers
app.include_router(sync_router)
app.include_router(async_router)
app.include_router(fake_router)
