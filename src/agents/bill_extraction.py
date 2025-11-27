"""
Bill Extraction Agent
Uploads medical bill or EOB (image/PDF) and extracts structured data.
Uses google.genai client for extraction.
"""

import logging
from typing import Union
from pathlib import Path
from google import genai
from google.genai import types

from utils.config import Config
from utils.image_utils import load_image_part, validate_file_exists
from schemas import BILL_SCHEMA

logger = logging.getLogger(__name__)


class BillExtractionAgent:
    """
    Handles bill upload and extraction using genai client.
    This agent uses direct genai client for multimodal content processing.
    """

    def __init__(self):
        self.name = "BillExtractionAgent"
        self.description = "Uploads and extracts data from medical bills (PDF/images)"
        self.client = genai.Client(api_key=Config.GOOGLE_API_KEY)
        self.instruction = (
            "Extract all medical billing information from this image including: "
            "patient name, member id, date(s) of service, provider name, "
            "each line item with CPT code, description, charge amount, and total. "
            "Return strict JSON following the schema."
        )
        logger.info(f"✅ {self.name} initialized")

    def extract(self, file_path: Union[str, Path]) -> str:
        """
        Extract bill data from an image or PDF file.

        Args:
            file_path: Path to the medical bill file

        Returns:
            Extracted bill data as JSON string
        """
        logger.info(f"🔍 {self.name}: Starting extraction from {file_path}")

        try:
            # Validate file exists
            validated_path = validate_file_exists(file_path)

            # Load image content
            image_content = load_image_part(validated_path, self.instruction)

            # Configure extraction
            config = types.GenerateContentConfig(
                system_instruction=self.instruction,
                temperature=Config.TEMPERATURE,
                response_mime_type="application/json",
                response_schema=BILL_SCHEMA,
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE
                    )
                ]
            )

            # Extract data
            response = self.client.models.generate_content(
                model=Config.DEFAULT_MODEL,
                contents=image_content.parts,
                config=config
            )

            logger.info(f"✅ {self.name}: Extraction complete ({len(response.text)} chars)")
            return response.text

        except Exception as e:
            logger.error(f"❌ {self.name}: Extraction failed - {e}", exc_info=True)
            raise


