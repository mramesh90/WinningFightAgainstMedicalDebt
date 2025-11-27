"""
Duplicate Charges Auditor
Identifies duplicate charges in medical bills using Google ADK Agent.
"""

import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.agent_wrapper import AgentWrapper
from google.adk.tools import google_search

logger = logging.getLogger(__name__)


class DuplicateChargesAuditor:
    """
    Auditor that identifies duplicate charges using Google ADK Agent.
    """

    def __init__(self):
        self.name = "DuplicateChargesAuditor"
        self.description = "Identifies duplicate charges in medical bills"

        self.agent_wrapper = AgentWrapper(
            name=self.name,
            model_name="gemini-2.5-flash-lite",
            instruction=(
                "You are a medical billing auditor specializing in duplicate charge detection. "
                "The user will provide JSON data with medical charges. "
                "Your job is to: "
                "1. Identify any duplicate charges (same CPT code, date, and amount appearing multiple times) "
                "2. Flag suspicious patterns (similar procedures billed multiple times on same day) "
                "3. Calculate the total amount of duplicate charges "
                "4. Provide specific recommendations for each duplicate found "
                "Add a 'duplicate_audit' section to the JSON with: "
                "- 'duplicates_found': list of duplicate charges with indices "
                "- 'total_duplicate_amount': sum of duplicate charges "
                "- 'recommendations': specific actions to take "
                "Return the complete, updated JSON."
            ),
            output_key="duplicate_audit_data",
            tools=[google_search]
        )

        logger.info(f"✅ {self.name} initialized with Google ADK Agent")

    async def audit(self, charges_data: str) -> str:
        """
        Audit charges for duplicates.

        Args:
            charges_data: JSON string containing charges data

        Returns:
            Audit results as string
        """
        logger.info(f"🔍 {self.name}: Starting duplicate detection")

        try:
            result = await self.agent_wrapper.run(charges_data)
            logger.info(f"✅ {self.name}: Audit complete")
            return result

        except Exception as e:
            logger.error(f"❌ {self.name}: Audit failed - {e}", exc_info=True)
            raise

