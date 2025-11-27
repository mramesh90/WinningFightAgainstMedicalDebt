"""
Configuration management for the application.
"""

import os
import logging

logger = logging.getLogger(__name__)


class Config:
    """Application configuration."""

    # API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # Model Configuration
    DEFAULT_MODEL = "gemini-2.5-flash-lite"
    TEMPERATURE = 0.1

    # Poppler Configuration (Windows)
    POPPLER_BIN_PATH = r"C:\Ramesh\Software\poppler-windows\Release-25.11.0-0\poppler-25.11.0\Library\bin"

    # File Paths
    BILLS_DIR = "bills"

    @classmethod
    def validate(cls):
        """Validates that required configuration is set."""
        if not cls.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY environment variable not set.")
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        logger.info("✅ Configuration validated successfully.")
        return True

