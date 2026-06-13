# dependencies.py
"""FastAPI dependency for extracting the authenticated user from a Bearer token."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_utils import verify_token
from logger import logger

bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Extract and verify the JWT from the Authorization header."""
    try:
        logger.debug("Dependency get_current_user invoked in LLM gateway")
        user_info = verify_token(credentials.credentials)
        return user_info
    except ValueError as val_err:
        logger.warning(f"Unauthorized request block in dependency: {val_err}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user dependency: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )
