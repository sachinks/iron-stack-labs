# streaming.py
from openai import AsyncOpenAI
from config import settings
from logger import logger

async def stream_tokens(message: str):
    try:
        logger.info(f"Initiating token stream for message of length {len(message)}")
        logger.debug(f"Prompt content: {message}")
        
        client = AsyncOpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama"
        )
    except Exception as e:
        logger.error(f"Failed to initialize AsyncOpenAI client: {e}", exc_info=True)
        yield {"data": f"[ERROR] Failed to initialize client: {str(e)}"}
        return

    try:
        stream = await client.chat.completions.create(
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "user", "content": message}],
            max_tokens=settings.MAX_TOKENS,
            stream=True
        )

        token_count = 0
        async for chunk in stream:
            try:
                token = chunk.choices[0].delta.content
                if token:
                    token_count += 1
                    yield {"data": token}
            except Exception as inner_e:
                logger.error(f"Error parsing chunk choices: {inner_e}", exc_info=True)

        logger.info(f"Stream completed successfully. Total tokens streamed: {token_count}")
        yield {"data": "[DONE]"}

    except Exception as e:
        logger.error(f"Error occurred during LLM token streaming: {e}", exc_info=True)
        yield {"data": f"[ERROR] {str(e)}"}

    finally:
        try:
            await client.close()
            logger.debug("AsyncOpenAI client connection closed successfully")
        except Exception as close_e:
            logger.error(f"Error closing AsyncOpenAI client: {close_e}", exc_info=True)
