"""
Main Orchestrator - Coordinates all agents in the medical bill processing workflow.
Main orchestrator that triggers and manages the entire flow.
"""

import logging
from pathlib import Path
from typing import Union
from .agent_wrapper import AgentWrapper

from agents import (
    BillExtractionAgent,
    ChargeExtractionAgent,
    DuplicateChargesAuditor,
    WrongCodesAuditor,
    ChargeExplainer,
    GoverningAgent
)

logger = logging.getLogger(__name__)


class MedicalBillOrchestrator:
    """
    Main orchestrator for the medical bill processing workflow.

    Workflow:
    1. BillExtractionAgent - Upload and extract bill data
    2. ChargeExtractionAgent - Extract charges and codes
    3. Parallel Agents (using ParallelAgent):
       - DuplicateChargesAuditor - Identify duplicate charges
       - WrongCodesAuditor - Validate CPT codes
       - ChargeExplainer - Explain charges in plain English
    4. GoverningAgent - Monitor and track execution
    """

    def __init__(self):
        logger.info("🔧 Initializing Medical Bill Orchestrator...")

        # Initialize Governing Agent
        self.governing_agent = GoverningAgent()

        # Bill Extraction (uses genai client directly)
        self.bill_extractor = BillExtractionAgent()

        # Charge Extraction (Google ADK Agent)
        self.charge_extractor = ChargeExtractionAgent()

        # Auditor and Explainer Agents (Google ADK Agents)
        self.duplicate_auditor = DuplicateChargesAuditor()
        self.code_auditor = WrongCodesAuditor()
        self.charge_explainer = ChargeExplainer()

        # Create ParallelAgent for auditors and explainer (all 3 run in parallel)
        self.parallel_auditors = AgentWrapper(
            name="ParallelAuditorsAndExplainer",
            agent_type="ParallelAgent",
            sub_agents=[
                self.duplicate_auditor.agent_wrapper.agent,
                self.code_auditor.agent_wrapper.agent,
                self.charge_explainer.agent_wrapper.agent
            ]
        )

        logger.info("✅ Orchestrator initialized with all agents")

    async def process_bill(self, bill_file_path: Union[str, Path]) -> dict:
        """
        Process a medical bill through the complete workflow.

        Args:
            bill_file_path: Path to the medical bill file

        Returns:
            Complete processing results
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🏥 STARTING MEDICAL BILL PROCESSING")
        logger.info(f"{'='*80}\n")
        logger.info(f"📄 File: {bill_file_path}")

        self.governing_agent.start_workflow()

        results = {
            "bill_file": str(bill_file_path),
            "status": "IN_PROGRESS",
            "stages": {}
        }

        try:
            # ========== STAGE 1: Bill Extraction ==========
            self.governing_agent.log_agent_execution("BillExtraction", "STARTED")
            logger.info("\n" + "─"*80)
            logger.info("STAGE 1: BILL EXTRACTION")
            logger.info("─"*80)

            extracted_data = self.bill_extractor.extract(bill_file_path)
            results["stages"]["bill_extraction"] = {
                "status": "SUCCESS",
                "data": extracted_data
            }
            self.governing_agent.log_agent_execution("BillExtraction", "SUCCESS", f"({len(extracted_data)} chars)")

            # ========== STAGE 2: Charge Extraction ==========
            self.governing_agent.log_agent_execution("ChargeExtraction", "STARTED")
            logger.info("\n" + "─"*80)
            logger.info("STAGE 2: CHARGE & CODE EXTRACTION")
            logger.info("─"*80)

            charges_data = await self.charge_extractor.extract(extracted_data)
            results["stages"]["charge_extraction"] = {
                "status": "SUCCESS",
                "data": charges_data
            }
            self.governing_agent.log_agent_execution("ChargeExtraction", "SUCCESS")

            # ========== STAGE 3: Parallel Auditing & Explanation ==========
            logger.info("\n" + "─"*80)
            logger.info("STAGE 3: PARALLEL AUDITING & EXPLANATION")
            logger.info("─"*80)
            logger.info("🔀 Running 3 agents in parallel:")
            logger.info("   • Duplicate Charges Auditor")
            logger.info("   • Wrong Codes Auditor")
            logger.info("   • Charge Explainer")

            self.governing_agent.log_agent_execution("DuplicateAuditor", "STARTED")
            self.governing_agent.log_agent_execution("CodeAuditor", "STARTED")
            self.governing_agent.log_agent_execution("ChargeExplainer", "STARTED")

            # Run parallel agents
            parallel_results = await self.parallel_auditors.run(charges_data)

            results["stages"]["parallel_analysis"] = {
                "status": "SUCCESS",
                "data": str(parallel_results)
            }

            self.governing_agent.log_agent_execution("DuplicateAuditor", "SUCCESS")
            self.governing_agent.log_agent_execution("CodeAuditor", "SUCCESS")
            self.governing_agent.log_agent_execution("ChargeExplainer", "SUCCESS")

            # Mark as complete
            results["status"] = "COMPLETED"
            results["final_output"] = str(parallel_results)

            logger.info("\n" + "="*80)
            logger.info("✅ BILL PROCESSING COMPLETED SUCCESSFULLY")
            logger.info("="*80 + "\n")

        except Exception as e:
            logger.error(f"\n❌ BILL PROCESSING FAILED: {e}", exc_info=True)
            results["status"] = "FAILED"
            results["error"] = str(e)
            self.governing_agent.log_agent_execution("Orchestrator", "FAILED", str(e))

        finally:
            # End workflow and generate report
            self.governing_agent.end_workflow()
            results["governance_report"] = self.governing_agent.generate_report()

        return results

