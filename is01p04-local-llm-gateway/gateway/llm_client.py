# llm_client.py
"""LLM client initialization wrapper."""
from openai import AsyncOpenAI
from config import settings
from logger import logger

def get_llm_client() -> AsyncOpenAI:
    """Retrieve an initialized AsyncOpenAI client."""
    try:
        logger.info(f"Initializing AsyncOpenAI client targeting base_url: {settings.llm_base_url}")
        client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url or None,
        )
        logger.debug("Successfully created AsyncOpenAI client")
        return client
    except Exception as e:
        logger.error(f"Error instantiating AsyncOpenAI client: {e}", exc_info=True)
        raise e
