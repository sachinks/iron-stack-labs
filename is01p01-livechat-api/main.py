# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from config import settings
from logger import logger
from models import ChatRequest
from streaming import stream_tokens

app = FastAPI(title="Iron Stack — LiveChat API")

@app.get("/health")
async def health():
    try:
        logger.info("Health check endpoint invoked")
        response_data = {"status": "healthy"}
        logger.debug(f"Health check succeeded, payload: {response_data}")
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        logger.error(f"Health check failed with error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        logger.info(f"Chat request received. Message length: {len(request.message)}")
        logger.debug(f"Payload: {request.message}")
        
        # Validate that the message is not just whitespace
        if not request.message.strip():
            logger.warning("Rejecting chat request: message consists only of whitespace")
            raise HTTPException(status_code=422, detail="Message cannot be empty or only whitespace")
            
        logger.info("Chat request validated, initiating SSE stream response")
        return EventSourceResponse(stream_tokens(request.message))
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


