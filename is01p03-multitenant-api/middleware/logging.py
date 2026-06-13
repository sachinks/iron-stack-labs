# logging.py
"""Request logging middleware tracking timings and hashing client IPs."""
import time
import hashlib
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from logger import logger as app_logger

# Define a child logger for structured request tracking
logger = logging.getLogger("is01p03-multitenant-api.request")

def _hash_ip(ip: str) -> str:
    try:
        return hashlib.sha256(ip.encode()).hexdigest()[:8]
    except Exception as e:
        app_logger.error(f"Failed to hash IP '{ip}': {e}", exc_info=True)
        return "unknown"

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            req_id = uuid.uuid4().hex[:8]
            request.state.req_id = req_id
            
            client_ip = request.client.host if request.client else "unknown"
            ip_hash = _hash_ip(client_ip)
            
            start = time.perf_counter()
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            
            resp_size = response.headers.get("content-length", "?")
            
            logger.info(
                f"{request.method} {request.url.path} → {response.status_code} "
                f"in {duration_ms:.1f}ms | req_id={req_id} | ip={ip_hash} | resp={resp_size}b"
            )
            return response
        except Exception as e:
            app_logger.error(f"Unexpected error in RequestLoggerMiddleware: {e}", exc_info=True)
            # Make sure we don't block the request if logger fails
            return await call_next(request)
