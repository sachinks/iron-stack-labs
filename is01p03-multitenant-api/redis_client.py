# redis_client.py
"""Shared async Redis client for the multitenant API.

Every module that needs Redis (rate limiting, caching, etc.)
imports `redis_client` from here — one connection, one place to configure.
"""
import redis.asyncio as aioredis
from config import settings
from logger import logger

try:
    logger.info(f"Initializing Async Redis connection pool at URL: {settings.redis_url}")
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to create Redis client from URL {settings.redis_url}: {e}", exc_info=True)
    raise e
