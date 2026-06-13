# main.py
"""Main application entry point for the Multitenant API."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from config import settings
from logger import logger
from redis_client import redis_client
from models import TENANT_DATA
from auth.routes import router as auth_router

from middleware.rate_limit import RateLimitMiddleware
from middleware.auth import AuthMiddleware
from middleware.logging import RequestLoggerMiddleware
from middleware.gdpr_logger import GDPRLoggerMiddleware

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

# Mount middlewares in LIFO stack order (reverse execution order)
# Execution Order: GDPRLoggerMiddleware -> RequestLoggerMiddleware -> AuthMiddleware -> RateLimitMiddleware -> Router
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(RequestLoggerMiddleware)
app.add_middleware(GDPRLoggerMiddleware)

# Include Auth login router
app.include_router(auth_router)

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

@app.get("/me")
async def me(request: Request):
    """Return current authenticated user profile."""
    try:
        logger.info("Endpoint /me called")
        user = getattr(request.state, "user", None)
        if not user:
            logger.warning("/me endpoint hit without authenticated user context")
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        response_data = {"user_id": user["sub"], "tier": user["tier"]}
        logger.debug(f"/me returning profile: {response_data}")
        return JSONResponse(content=response_data, status_code=200)
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(f"Error in /me endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/data/{user_id}")
async def get_data(user_id: str, request: Request):
    """Retrieve tenant isolated data."""
    try:
        logger.info(f"Endpoint /data/{user_id} called")
        user = getattr(request.state, "user", None)
        if not user:
            logger.warning("/data endpoint hit without authenticated user context")
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        # Cross-tenant check: user cannot query another tenant's data
        if user["sub"] != user_id:
            logger.warning(f"Cross-tenant access attempt: user '{user['sub']}' tried to access user '{user_id}' data")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied — you can only access your own data."
            )
            
        data = TENANT_DATA.get(user_id, {})
        response_data = {"user_id": user_id, "data": data}
        logger.debug(f"/data/{user_id} returning data: {response_data}")
        return JSONResponse(content=response_data, status_code=200)
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(f"Error in /data/{user_id} endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
