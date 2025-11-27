"""
Charge & Procedure Code Extraction Agent
Extracts charges and procedure codes from bill data using Google ADK Agent.
"""

import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.agent_wrapper import AgentWrapper
from google.adk.tools import google_search

logger = logging.getLogger(__name__)


class ChargeExtractionAgent:
    """
    Extracts charges and procedure codes using Google ADK Agent.
    """

    def __init__(self):
        self.name = "ChargeExtractionAgent"
        self.description = "Extracts charges and procedure codes from bill data"

        self.agent_wrapper = AgentWrapper(
            name=self.name,
            model_name="gemini-2.5-flash-lite",
            instruction=(
                "You are a medical billing data extractor. "
                "The user will provide JSON data from a medical bill. "
                "Extract and structure all charges and CPT procedure codes. "
                "List each charge with: date, description, CPT code, and amount. "
                "Return the complete, structured JSON with all charges clearly organized."
            ),
            output_key="charges_data",
            tools=[google_search]
        )

        logger.info(f"✅ {self.name} initialized with Google ADK Agent")

    async def extract(self, bill_data: str) -> str:
        """
        Extract charges and codes from bill data.

        Args:
            bill_data: JSON string containing bill data

        Returns:
            Structured charges and codes as string
        """
        logger.info(f"🔍 {self.name}: Starting charge extraction")

        try:
            result = await self.agent_wrapper.run(bill_data)
            logger.info(f"✅ {self.name}: Extraction complete")
            return result

        except Exception as e:
            logger.error(f"❌ {self.name}: Extraction failed - {e}", exc_info=True)
            raise

