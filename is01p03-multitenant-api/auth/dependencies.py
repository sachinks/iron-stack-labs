# dependencies.py
"""Dependency injection for extracting user/tenant data from JWT."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.jwt_utils import verify_token
from logger import logger

bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """FastAPI dependency to extract and verify current user credentials."""
    try:
        logger.debug("Dependency get_current_user invoked")
        token = credentials.credentials
        user_info = verify_token(token)
        logger.debug(f"Dependency get_current_user retrieved user sub='{user_info.get('sub')}'")
        return user_info
    except ValueError as val_err:
        logger.warning(f"Unauthorized access attempt: {val_err}")
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
