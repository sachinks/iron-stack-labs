# jwt_utils.py
"""JWT token verification for the LLM gateway.

This module only *verifies* tokens — it does not issue them.
Tokens are issued by IS01P03 (multitenant API) using the same
shared secret. This is the standard microservice pattern:
shared secret, independent verification.
"""
from jose import jwt, JWTError
from config import settings
from logger import logger

def verify_token(token: str) -> dict:
    """Decode and verify a JWT access token."""
    try:
        logger.debug("Attempting to verify JWT token in LLM gateway")
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        logger.debug(f"Successfully verified token for sub='{payload.get('sub')}'")
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise ValueError(f"Invalid token: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error in verify_token: {e}", exc_info=True)
        raise e
