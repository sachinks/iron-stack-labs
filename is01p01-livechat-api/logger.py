# logger.py
import os
import logging
from logging.handlers import RotatingFileHandler
from config import settings

try:
    # Ensure logs folder exists
    os.makedirs("logs", exist_ok=True)
    
    logger = logging.getLogger("is01p01-livechat-api")
    logger.setLevel(settings.LOG_LEVEL.upper())
    
    # Configure handlers if not already configured
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
    # Basic console warning print as a last resort
    print(f"Error initializing custom logger: {e}")
