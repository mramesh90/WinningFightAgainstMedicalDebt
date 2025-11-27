"""
Wrong Codes Auditor
Identifies incorrect or invalid CPT codes using Google ADK Agent.
"""

import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.agent_wrapper import AgentWrapper
from google.adk.tools import google_search

logger = logging.getLogger(__name__)


class WrongCodesAuditor:
    """
    Auditor that identifies wrong/invalid CPT codes using Google ADK Agent.
    """

    def __init__(self):
        self.name = "WrongCodesAuditor"
        self.description = "Identifies incorrect or invalid CPT codes"

        self.agent_wrapper = AgentWrapper(
            name=self.name,
            model_name="gemini-2.5-flash-lite",
            instruction=(
                "You are a medical billing auditor specializing in CPT code validation. "
                "The user will provide JSON data with medical charges and CPT codes. "
                "Your job is to: "
                "1. Validate each CPT code format (should be 5 digits) "
                "2. Identify deprecated or obsolete codes (like 99201-99205 discontinued in 2021) "
                "3. Check for unbundling issues (procedures that should be billed together) "
                "4. Identify suspicious or unusual codes for the described procedure "
                "5. Use Google Search to verify current CPT code standards and typical costs "
                "Add a 'code_audit' section to the JSON with: "
                "- 'invalid_codes': list of format issues "
                "- 'deprecated_codes': list of outdated codes "
                "- 'suspicious_codes': codes that don't match procedure descriptions "
                "- 'pricing_alerts': charges significantly above market rates "
                "- 'recommendations': specific actions to take "
                "Return the complete, updated JSON."
            ),
            output_key="code_audit_data",
            tools=[google_search]
        )

        logger.info(f"✅ {self.name} initialized with Google ADK Agent")

    async def audit(self, charges_data: str) -> str:
        """
        Audit CPT codes for errors.

        Args:
            charges_data: JSON string containing charges data

        Returns:
            Audit results as string
        """
        logger.info(f"🔍 {self.name}: Starting code validation")

        try:
            result = await self.agent_wrapper.run(charges_data)
            logger.info(f"✅ {self.name}: Audit complete")
            return result

        except Exception as e:
            logger.error(f"❌ {self.name}: Audit failed - {e}", exc_info=True)
            raise

