# logger.py
"""Level-based rotating file and console logger for the LLM Gateway."""
import os
import logging
from logging.handlers import RotatingFileHandler
from config import settings

try:
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    logger = logging.getLogger("is01p04-local-llm-gateway")
    logger.setLevel(settings.LOG_LEVEL.upper())
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
        )
        
        # Console stdout handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Rotating file handler (5 MB size, 5 backups)
        file_handler = RotatingFileHandler(
            "logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
except Exception as e:
    print(f"Error initializing custom logger for is01p04: {e}")
