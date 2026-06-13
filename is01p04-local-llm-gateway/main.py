# main.py
"""Main application entry point for the Local LLM Gateway."""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from config import settings
from logger import logger
from gateway.llm_client import get_llm_client
from auth.dependencies import get_current_user

app = FastAPI(title="Iron Stack — Local LLM Gateway")

@app.get("/health")
async def health():
    """Simple health check endpoint."""
    try:
        logger.info("Health check endpoint called")
        response_data = {"status": "ok"}
        logger.debug(f"Health check status: {response_data}")
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        logger.error(f"Error in health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/chat")
async def chat(request: Request, user: dict = Depends(get_current_user)):
    """Chat completions endpoint that streams model tokens via EventSourceResponse."""
    try:
        logger.info(f"Chat completions called by user_id='{user.get('sub')}' (tier='{user.get('tier')}')")
        body = await request.json()
        prompt = body.get("prompt", "")
        if not prompt.strip():
            logger.warning("Empty prompt received in chat completions")
            raise HTTPException(status_code=422, detail="Prompt message cannot be empty")
            
        client = get_llm_client()
        
        async def token_stream():
            try:
                logger.info(f"Starting async token stream to Ollama for prompt: {prompt[:50]}...")
                stream = await client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                )
                async for chunk in stream:
                    # Capture token chunk content safely
                    tok = chunk.choices[0].delta.content
                    if tok:
                        logger.debug(f"Yielding token: {repr(tok)}")
                        yield tok
                # SSE final token signal
                logger.info("Token stream successfully completed. Yielding [DONE]")
                yield "[DONE]"
            except Exception as stream_e:
                logger.error(f"Error encountered inside token generator stream: {stream_e}", exc_info=True)
                yield f"[ERROR] {stream_e}"
                
        return EventSourceResponse(token_stream())
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        logger.error(f"Error preparing chat completions stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
