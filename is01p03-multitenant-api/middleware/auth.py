# auth.py
"""Authentication middleware to extract and verify JWT on protected routes."""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from auth.jwt_utils import verify_token
from logger import logger

PUBLIC_PATHS = {"/health", "/auth/login", "/docs", "/openapi.json"}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            logger.debug(f"AuthMiddleware processing request: {request.method} {request.url.path}")
            
            # Check if path is public
            if request.url.path in PUBLIC_PATHS:
                logger.debug(f"Path '{request.url.path}' is public. Skipping authentication.")
                request.state.user = None
                return await call_next(request)
                
            # Extract Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                logger.warning("Missing Authorization header on protected route")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing Authorization header"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            # Check Bearer format
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                logger.warning("Malformed Authorization header on protected route")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Malformed Authorization header"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            token = parts[1]
            try:
                user_info = verify_token(token)
                request.state.user = user_info
                logger.debug(f"AuthMiddleware authenticated user: {user_info.get('sub')}")
            except ValueError as val_err:
                logger.warning(f"Invalid token: {val_err}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unexpected error in AuthMiddleware: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during authentication"}
            )
