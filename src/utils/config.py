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

    # Poppler Configuration
    POPPLER_BIN_PATH = os.getenv("POPPLER_BIN_PATH")

    # File Paths
    BILLS_DIR = "bills"

    # Session Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///medical_bill_agent_data.db")
    APP_NAME = "medical_bill_processing"

    # Events Compaction Configuration
    COMPACTION_INTERVAL = 3  # Trigger compaction every 3 invocations
    OVERLAP_SIZE = 1  # Keep 1 previous turn for context

    @classmethod
    def validate(cls):
        """Validates that required configuration is set."""
        if not cls.GOOGLE_API_KEY:
            logger.error("GOOGLE_API_KEY environment variable not set.")
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        logger.info("✅ Configuration validated successfully.")
        logger.info(f"   Database: {cls.DATABASE_URL}")
        logger.info(f"   App Name: {cls.APP_NAME}")
        logger.info(f"   Compaction Interval: {cls.COMPACTION_INTERVAL}")
        return True

