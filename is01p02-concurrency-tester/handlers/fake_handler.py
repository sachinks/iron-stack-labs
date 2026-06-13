# handlers/fake_handler.py
import asyncio
from fastapi import APIRouter, HTTPException
from logger import logger

router = APIRouter()

@router.get("/fake")
async def fake() -> dict:
    try:
        logger.info("Fake async sleep handler called")
        await asyncio.sleep(2)
        logger.debug("Fake sleep handler completed successfully")
        return {"response": "fake"}
    except Exception as e:
        logger.error(f"Error in fake handler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fake sleep failed")
