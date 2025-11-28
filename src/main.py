"""
Main Entry Point for Winning the Fight Against Medical Debt.
Production-ready application using Google ADK agents with proper orchestration.
"""

import asyncio
import sys
from asyncio import WindowsSelectorEventLoopPolicy
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from observability import setup_logging
from orchestrator import MedicalBillOrchestrator
from utils import Config
import logging

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""

    # Setup logging
    setup_logging(log_level="INFO", log_to_file=True, log_dir="logs")

    logger.info("=" * 80)
    logger.info("MEDICAL BILL PROCESSING SYSTEM - PRODUCTION VERSION")
    logger.info("Using Google ADK Agents (Agent, ParallelAgent, SequentialAgent)")
    logger.info("=" * 80)

    try:
        # Validate configuration
        Config.validate()

        # Initialize main orchestrator
        orchestrator = MedicalBillOrchestrator()

        # Get bill file path
        script_dir = Path(__file__).parent
        bill_file = script_dir / "bills" / "Sample_bill.pdf"

        if not bill_file.exists():
            logger.error(f"❌ Bill file not found: {bill_file}")
            logger.info("Please ensure a bill file exists in the 'bills' directory")
            return

        # Process the bill through the complete workflow
        results = await orchestrator.process_bill(bill_file)

        # Print final results
        print("\n" + "=" * 80)
        print("FINAL PROCESSING RESULTS")
        print("=" * 80)
        print(f"\n📄 File: {results['bill_file']}")
        print(f"✅ Status: {results['status']}")
        print(f"\n📊 Stages Completed: {len(results['stages'])}")

        for stage_name, stage_data in results['stages'].items():
            print(f"   • {stage_name}: {stage_data['status']}")

        # Print final output
        if 'final_output' in results:
            print("\n" + "─" * 80)
            print("FINAL ANALYSIS OUTPUT")
            print("─" * 80)
            print(results['final_output'])

        # Print governance report
        print("\n")
        orchestrator.governing_agent.print_report()

        logger.info("✅ Processing completed successfully")

    except Exception as e:
        logger.error(f"❌ Application failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Windows specific event loop policy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

