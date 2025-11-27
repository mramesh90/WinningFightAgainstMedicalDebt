"""
Charge Explainer
Explains medical charges in plain English using Google ADK Agent.
"""

import logging
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.agent_wrapper import AgentWrapper
from google.adk.tools import google_search

logger = logging.getLogger(__name__)


class ChargeExplainer:
    """
    Explains medical charges in plain English using Google ADK Agent.
    """

    def __init__(self):
        self.name = "ChargeExplainer"
        self.description = "Explains medical charges in plain English"

        self.agent_wrapper = AgentWrapper(
            name=self.name,
            model_name="gemini-2.5-flash-lite",
            instruction=(
                "You are a medical billing translator who helps patients understand their bills. "
                "The user will provide JSON data with medical charges and CPT codes. "
                "Your job is to: "
                "1. Add a 'plain_english_description' to each line item explaining what the procedure actually is "
                "2. Use simple, patient-friendly language (avoid medical jargon) "
                "3. Explain WHY this procedure/service was necessary "
                "4. Use Google Search to find accurate, current information about each CPT code "
                "5. Include typical cost ranges from your research "
                "6. Add context about whether the charge seems reasonable "
                "For example, instead of 'CPT 99213 - Office Visit', explain: "
                "'Office visit with your doctor to discuss your condition (typically 15-30 minutes). "
                "This is a standard follow-up visit. Typical cost: $100-$200.' "
                "Return the complete, updated JSON with all plain English explanations added."
            ),
            output_key="explained_data",
            tools=[google_search]
        )

        logger.info(f"✅ {self.name} initialized with Google ADK Agent")

    async def explain(self, charges_data: str) -> str:
        """
        Explain charges in plain English.

        Args:
            charges_data: JSON string containing charges data

        Returns:
            Explained charges as string
        """
        logger.info(f"🔍 {self.name}: Starting charge explanation")

        try:
            result = await self.agent_wrapper.run(charges_data)
            logger.info(f"✅ {self.name}: Explanation complete")
            return result

        except Exception as e:
            logger.error(f"❌ {self.name}: Explanation failed - {e}", exc_info=True)
            raise

