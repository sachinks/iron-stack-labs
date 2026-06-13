# routes.py
"""Auth routes — login endpoint for the multitenant API.

Provides a POST /auth/login route that issues a JWT access token
for a given user_id and tier. Mounted on the main app via include_router().
"""
from fastapi import APIRouter, HTTPException, status
from auth.jwt_utils import create_access_token
from logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(user_id: str, tier: str = "free"):
    """Issue a JWT access token for the given user and tier."""
    try:
        logger.info(f"Login request received for user_id='{user_id}', tier='{tier}'")
        token = create_access_token(user_id, tier)
        logger.info(f"Successful login for user_id='{user_id}', token issued")
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login failed for user_id='{user_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to issue token"
        )
