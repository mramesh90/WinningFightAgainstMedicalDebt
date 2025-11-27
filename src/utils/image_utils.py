"""
Utility functions for image and PDF processing.
"""

import io
from pathlib import Path
from typing import Union
import PIL.Image
from pdf2image import convert_from_path
from google.genai import types
import logging
from .config import Config

logger = logging.getLogger(__name__)


def load_image_part(file_path: Union[str, Path], instruction: str) -> types.UserContent:
    """
    Converts an image or PDF file into a UserContent object for Gemini API.

    Args:
        file_path: Path to the image or PDF file
        instruction: Text instruction to accompany the image

    Returns:
        types.UserContent object ready for API consumption

    Raises:
        ValueError: If PDF is empty
        Exception: If PDF conversion fails
    """
    file_path = str(file_path)
    image_obj = None

    if file_path.lower().endswith('.pdf'):
        try:
            images = convert_from_path(file_path, poppler_path=Config.POPPLER_BIN_PATH)
            if not images:
                raise ValueError("PDF is empty")
            image_obj = images[0]
            logger.info(f"✅ Successfully converted PDF: {file_path}")
        except Exception as e:
            logger.error(f"❌ Failed to convert PDF: {file_path}")
            raise Exception(f"Failed to convert PDF. Check path: {Config.POPPLER_BIN_PATH}") from e
    else:
        image_obj = PIL.Image.open(file_path)
        logger.info(f"✅ Successfully loaded image: {file_path}")

    # Convert to bytes
    img_byte_arr = io.BytesIO()
    if image_obj.mode != 'RGB':
        image_obj = image_obj.convert('RGB')

    image_obj.save(img_byte_arr, format='JPEG')
    image_bytes = img_byte_arr.getvalue()

    # Create parts for API
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg"
    )
    text_part = types.Part(text=instruction)

    return types.UserContent(parts=[text_part, image_part])


def validate_file_exists(file_path: Union[str, Path]) -> Path:
    """
    Validates that a file exists.

    Args:
        file_path: Path to validate

    Returns:
        Path object if file exists

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at: {path}")
    return path

