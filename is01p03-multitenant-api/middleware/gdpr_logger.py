# gdpr_logger.py
"""GDPR compliance logging middleware that redacts sensitive auth details."""
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from logger import logger as app_logger

# Use a dedicated child logger for GDPR compliant tracing
gdpr_logger = logging.getLogger("is01p03-multitenant-api.gdpr")

class GDPRLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                auth = "Bearer [REDACTED]"
                
            response = await call_next(request)
            
            gdpr_logger.info(f"{request.method} {request.url.path} — {auth} — {response.status_code}")
            return response
        except Exception as e:
            app_logger.error(f"Unexpected error in GDPRLoggerMiddleware: {e}", exc_info=True)
            return await call_next(request)
