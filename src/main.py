"""
Main Entry Point for Medical Bill Processing System
Application using Google ADK agents with proper orchestration.
Includes persistent sessions using DatabaseSessionService for follow-up questions.
"""

import asyncio
import sys
from asyncio import WindowsSelectorEventLoopPolicy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from observability import setup_logging
from orchestrator import MedicalBillOrchestrator
from utils import Config
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.sessions import DatabaseSessionService
from google.adk.runners import Runner
from google.genai import types
import logging

logger = logging.getLogger(__name__)

APP_NAME = "medical_bill_app"
USER_ID = "default_user"
MODEL_NAME = "gemini-2.5-flash-lite"


async def run_session(runner_instance, user_queries, session_name, session_service):
    """
    Run a conversation session with the agent.

    Args:
        runner_instance: The Runner instance
        user_queries: List of queries or single query string
        session_name: Session identifier
        session_service: DatabaseSessionService instance
    """
    print(f"\n### Session: {session_name}")

    app_name = runner_instance.app_name

    # Create or retrieve session
    try:
        session = await session_service.create_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )
    except:
        session = await session_service.get_session(
            app_name=app_name, user_id=USER_ID, session_id=session_name
        )

    # Process queries
    if user_queries:
        if isinstance(user_queries, str):
            user_queries = [user_queries]

        for query in user_queries:
            print(f"\n👤 User > {query}")

            # Convert to ADK Content format
            query_content = types.Content(role="user", parts=[types.Part(text=query)])

            # Stream agent's response
            async for event in runner_instance.run_async(
                user_id=USER_ID, session_id=session.id, new_message=query_content
            ):
                if event.content and event.content.parts:
                    if event.content.parts[0].text and event.content.parts[0].text != "None":
                        print(f"🤖 {MODEL_NAME} > {event.content.parts[0].text}")


async def main():
    """Main application entry point with sessions."""

    # Setup logging
    setup_logging(log_level="INFO", log_to_file=True, log_dir="logs")

    logger.info("MEDICAL BILL PROCESSING ")

    try:
        # Validate configuration
        Config.validate()

        # ======================================================================
        # SETUP: Initialize DatabaseSessionService FIRST
        # ======================================================================
        print("\n📋 Setting up Shared Session Service...")
        db_url = "sqlite+aiosqlite:///medical_bill_agent_data.db"
        session_service = DatabaseSessionService(db_url=db_url)
        print(f"✅ DatabaseSessionService created: {db_url}")

        # Create shared session ID for this bill processing workflow
        SHARED_SESSION_ID = "bill-analysis-session"
        print(f"✅ Using shared session: {SHARED_SESSION_ID}")
        print("   All agents will write to this session, chatbot will read from it!")

        # ======================================================================
        # PART 1: PROCESS MEDICAL BILL (Writing to Shared Session)
        # ======================================================================
        print("PART 1: BILL PROCESSING (Writing to Session)")

        logger.info("INITIALIZING ORCHESTRATOR")
        orchestrator = MedicalBillOrchestrator()

        # Get bill file path
        script_dir = Path(__file__).parent
        bill_file = script_dir / "bills" / "dummy_bill.pdf"

        if not bill_file.exists():
            logger.error(f"❌ Bill file not found: {bill_file}")
            logger.info("Creating sample results for demonstration...")

            # Sample results for demo
            results = {
                "bill_file": str(bill_file),
                "status": "COMPLETED",
                "stages": {
                    "bill_extraction": {"status": "SUCCESS", "data": "Sample extraction"},
                    "charge_extraction": {"status": "SUCCESS", "data": "Office Visit: $150, Lab Work: $300, Total: $450"},
                    "parallel_analysis": {"status": "SUCCESS", "data": "No duplicates. All codes valid. Charges explained."}
                },
                "final_output": "Bill analysis complete. Total: $450. No issues found."
            }
        else:
            # Process the bill
            results = await orchestrator.process_bill(bill_file)

        # Print results
        print("BILL PROCESSING RESULTS")
        print(f"\n📄 File: {results['bill_file']}")
        print(f"✅ Status: {results['status']}")
        print(f"\n📊 Stages Completed: {len(results['stages'])}")

        for stage_name, stage_data in results['stages'].items():
            print(f"   • {stage_name}: {stage_data['status']}")

        if 'final_output' in results:
            print("ANALYSIS OUTPUT")
            print(results['final_output'])

        # ======================================================================
        # Write bill results to the SHARED SESSION
        # ======================================================================
        print("\n📝 Writing bill analysis results to shared session...")

        # Create a summary agent to write results to session
        retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )

        summary_agent = LlmAgent(
            model=Gemini(model=MODEL_NAME, retry_options=retry_config),
            name="bill_summary_agent",
            description="Agent that writes bill analysis to session",
        )

        summary_runner = Runner(agent=summary_agent, app_name=APP_NAME, session_service=session_service)

        # Write detailed results to session
        bill_summary = f"""I have completed analyzing a medical bill. Here are the comprehensive results:

FILE INFORMATION:
- Bill File: {results['bill_file']}
- Processing Status: {results['status']}

CHARGE EXTRACTION:
{results.get('stages', {}).get('charge_extraction', {}).get('data', 'No charge data available')}

DETAILED ANALYSIS:
{results.get('stages', {}).get('parallel_analysis', {}).get('data', 'No analysis data available')}

FINAL OUTPUT:
{results.get('final_output', 'No final output available')}

You can now answer any questions about this bill analysis."""

        # Write to shared session
        await run_session(
            summary_runner,
            [bill_summary],
            SHARED_SESSION_ID,
            session_service
        )
        print("✅ Bill analysis written to session!")

        # ======================================================================
        # PART 2: INTERACTIVE Q&A 
        # ======================================================================
        print("PART 2: INTERACTIVE Q&A (Reading from Same Session)")

        # Create chatbot that will read from the SAME session
        print("\n📋 Creating chatbot agent (will read from shared session)...")
        chatbot_agent = LlmAgent(
            model=Gemini(model=MODEL_NAME, retry_options=retry_config),
            name="medical_bill_chatbot",
            description="A medical bill chatbot that answers questions about bill analysis",
        )

        chatbot_runner = Runner(agent=chatbot_agent, app_name=APP_NAME, session_service=session_service)
        print("✅ Chatbot created - connected to shared session!")
        print("   💡 Chatbot can now see all the bill analysis results from the session!")

        # Ask follow-up questions - chatbot reads from SAME session!
        print("FOLLOW-UP QUESTIONS (Chatbot reads from shared session)")

        await run_session(
            chatbot_runner,
            [
                "What was the total amount on the bill?",
                "Is that amount reasonable?",
                "Were any duplicate charges found?",
            ],
            SHARED_SESSION_ID,
            session_service
        )

        # Interactive mode
        print("INTERACTIVE MODE")
        print("You can now ask follow-up questions about the bill.")
        print("The chatbot has access to ALL bill analysis results from the shared session!")
        print("Type 'quit' or 'exit' to end the session.")

        while True:
            try:
                user_input = input("\n👤 Your question: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                if user_input:
                    await run_session(
                        chatbot_runner,  # Use chatbot runner
                        [user_input],
                        SHARED_SESSION_ID,  # SAME shared session!
                        session_service
                    )
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Session ended.")
                break

        logger.info("✅ Processing completed successfully")

    except Exception as e:
        logger.error(f"❌ Application failed: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Windows specific event loop policy
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

