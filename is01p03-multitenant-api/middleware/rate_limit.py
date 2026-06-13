# rate_limit.py
"""Rate limiting middleware using Redis state."""
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import TIER_LIMITS
from redis_client import redis_client
from logger import logger

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            logger.debug(f"RateLimitMiddleware processing request: {request.method} {request.url.path}")
            
            # Rate limiting only applies if request.state.user is set (authenticated requests)
            user = getattr(request.state, "user", None)
            if not user:
                logger.debug("No authenticated user context. Skipping rate limiting.")
                return await call_next(request)
                
            user_id = user["sub"]
            tier = user.get("tier", "free")
            limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
            
            window = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
            key = f"rate_limit:{user_id}:{window}"
            
            try:
                count = await redis_client.incr(key)
                if count == 1:
                    await redis_client.expire(key, 60)
            except Exception as redis_err:
                logger.error(f"Redis operation failed during rate limit check: {redis_err}", exc_info=True)
                # Fail-safe: allow request to proceed if Redis is down
                return await call_next(request)
                
            if count > limit:
                logger.warning(f"Rate limit exceeded for user_id='{user_id}' ({tier} tier, count={count}/{limit})")
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. Tier '{tier}' allows {limit} requests/min."}
                )
                
            logger.debug(f"Rate limit check passed for user_id='{user_id}' (count={count}/{limit})")
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unexpected error in RateLimitMiddleware: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during rate limiting"}
            )
