# jwt_utils.py
"""JWT token generation and verification utilities."""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from config import settings
from logger import logger

def create_access_token(user_id: str, tier: str) -> str:
    """Create a new JWT access token."""
    try:
        logger.info(f"Generating access token for user_id='{user_id}' with tier='{tier}'")
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "tier": tier,
            "exp": now + timedelta(minutes=settings.access_token_expire_mins),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        logger.debug("Successfully generated JWT token")
        return token
    except Exception as e:
        logger.error(f"Error creating access token for user_id='{user_id}': {e}", exc_info=True)
        raise e

def verify_token(token: str) -> dict:
    """Decode and verify a JWT access token."""
    try:
        logger.debug("Attempting to verify JWT token")
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        logger.debug(f"Successfully verified JWT token for sub='{payload.get('sub')}'")
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise ValueError(f"Invalid token: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}", exc_info=True)
        raise e
