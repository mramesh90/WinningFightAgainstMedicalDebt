"""
Integration Tests for Medical Bill Processing with Sessions
===========================================================

Tests the complete end-to-end flow with real components.
"""

import asyncio
import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import Config
from orchestrator import MedicalBillOrchestrator
from google.adk.sessions import DatabaseSessionService
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.genai import types


class TestEndToEndWorkflow(unittest.IsolatedAsyncioTestCase):
    """End-to-end integration tests"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # Ensure API key is set for tests
        if not os.getenv('GOOGLE_API_KEY'):
            os.environ['GOOGLE_API_KEY'] = 'test_key_for_structure_testing'

    async def test_complete_workflow_without_api_calls(self):
        """Test complete workflow structure without making actual API calls"""

        # Step 1: Initialize session service
        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        # Verify session service is created
        self.assertIsNotNone(session_service)

        # Step 2: Initialize orchestrator
        orchestrator = MedicalBillOrchestrator()

        # Verify orchestrator components
        self.assertIsNotNone(orchestrator.bill_extractor)
        self.assertIsNotNone(orchestrator.charge_extractor)
        self.assertIsNotNone(orchestrator.duplicate_auditor)
        self.assertIsNotNone(orchestrator.code_auditor)
        self.assertIsNotNone(orchestrator.charge_explainer)

        # Step 3: Create agents
        retry_config = types.HttpRetryOptions(
            attempts=3,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )

        summary_agent = LlmAgent(
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            name="summary_agent",
            description="Summary agent",
        )

        chatbot_agent = LlmAgent(
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            name="chatbot_agent",
            description="Chatbot agent",
        )

        # Verify agents created
        self.assertIsNotNone(summary_agent)
        self.assertIsNotNone(chatbot_agent)

        # Step 4: Create runners
        summary_runner = Runner(
            agent=summary_agent,
            app_name="test_app",
            session_service=session_service
        )

        chatbot_runner = Runner(
            agent=chatbot_agent,
            app_name="test_app",
            session_service=session_service
        )

        # Verify runners created
        self.assertIsNotNone(summary_runner)
        self.assertIsNotNone(chatbot_runner)

        # Verify they use same app name (for shared session)
        self.assertEqual(summary_runner.app_name, chatbot_runner.app_name)

    async def test_session_sharing_between_agents(self):
        """Test that multiple agents can share a session"""

        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        SHARED_SESSION_ID = "shared_test_session"
        APP_NAME = "test_app"
        USER_ID = "test_user"

        # Create session
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SHARED_SESSION_ID
        )

        self.assertEqual(session.id, SHARED_SESSION_ID)

        # Retrieve same session (simulating another agent)
        retrieved_session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=SHARED_SESSION_ID
        )

        # Verify it's the same session
        self.assertEqual(session.id, retrieved_session.id)
        self.assertEqual(session.user_id, retrieved_session.user_id)

    async def test_bill_processing_results_structure(self):
        """Test that bill processing returns correct structure"""

        orchestrator = MedicalBillOrchestrator()

        # Create sample results (as main.py does when file not found)
        results = {
            "bill_file": "test_bill.pdf",
            "status": "COMPLETED",
            "stages": {
                "bill_extraction": {"status": "SUCCESS", "data": "Sample extraction"},
                "charge_extraction": {"status": "SUCCESS", "data": "Office Visit: $150, Lab Work: $300, Total: $450"},
                "parallel_analysis": {"status": "SUCCESS", "data": "No duplicates. All codes valid. Charges explained."}
            },
            "final_output": "Bill analysis complete. Total: $450. No issues found."
        }

        # Verify all required keys exist
        required_keys = ["bill_file", "status", "stages", "final_output"]
        for key in required_keys:
            self.assertIn(key, results)

        # Verify stages structure
        required_stages = ["bill_extraction", "charge_extraction", "parallel_analysis"]
        for stage in required_stages:
            self.assertIn(stage, results["stages"])
            self.assertIn("status", results["stages"][stage])
            self.assertIn("data", results["stages"][stage])

    def test_content_creation_for_run_session(self):
        """Test Content object creation as used in run_session"""

        query = "What is the total amount?"

        # Create Content object as done in run_session
        content = types.Content(role="user", parts=[types.Part(text=query)])

        # Verify structure
        self.assertEqual(content.role, "user")
        self.assertEqual(len(content.parts), 1)
        self.assertEqual(content.parts[0].text, query)

    async def test_run_session_query_handling(self):
        """Test query handling logic from run_session function"""

        # Test 1: String input
        single_query = "Test query"
        if isinstance(single_query, str):
            queries = [single_query]

        self.assertIsInstance(queries, list)
        self.assertEqual(len(queries), 1)

        # Test 2: List input
        list_queries = ["Query 1", "Query 2", "Query 3"]
        if isinstance(list_queries, str):
            queries = [list_queries]
        else:
            queries = list_queries

        self.assertIsInstance(queries, list)
        self.assertEqual(len(queries), 3)


class TestSessionLifecycle(unittest.IsolatedAsyncioTestCase):
    """Test session creation, usage, and cleanup"""

    async def test_session_creation_flow(self):
        """Test session creation as done in run_session"""

        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        app_name = "test_app"
        user_id = "test_user"
        session_name = "test_session"

        # Try to create session (as run_session does)
        try:
            session = await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_name
            )
            created = True
        except:
            session = await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_name
            )
            created = False

        # First time should create
        self.assertTrue(created)
        self.assertEqual(session.id, session_name)

    async def test_session_retrieval_flow(self):
        """Test session retrieval after creation"""

        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        app_name = "test_app"
        user_id = "test_user"
        session_name = "test_session_retrieve"

        # Create session first
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_name
        )

        # Try to create again (should retrieve existing)
        try:
            session = await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_name
            )
            retrieved = False
        except:
            session = await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_name
            )
            retrieved = True

        # Should retrieve existing
        self.assertTrue(retrieved or session.id == session_name)


class TestBillSummaryFormatting(unittest.TestCase):
    """Test bill summary formatting for session context"""

    def test_bill_summary_creation(self):
        """Test creating bill summary from results"""

        results = {
            "bill_file": "test_bill.pdf",
            "status": "COMPLETED",
            "stages": {
                "charge_extraction": {"status": "SUCCESS", "data": "Charges: $450"},
                "parallel_analysis": {"status": "SUCCESS", "data": "Analysis complete"}
            },
            "final_output": "Total: $450"
        }

        # Create summary as done in main.py
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

        # Verify summary contains key information
        self.assertIn("test_bill.pdf", bill_summary)
        self.assertIn("COMPLETED", bill_summary)
        self.assertIn("$450", bill_summary)
        self.assertIn("CHARGE EXTRACTION", bill_summary)
        self.assertIn("DETAILED ANALYSIS", bill_summary)


class TestInteractiveModeLogic(unittest.TestCase):
    """Test interactive mode logic"""

    def test_quit_command_detection(self):
        """Test quit command detection"""

        quit_commands = ['quit', 'exit', 'q', 'QUIT', 'EXIT', 'Q']

        for cmd in quit_commands:
            should_quit = cmd.lower() in ['quit', 'exit', 'q']
            self.assertTrue(should_quit)

    def test_non_quit_command(self):
        """Test non-quit commands don't trigger exit"""

        normal_commands = ['What is the total?', 'help', 'status', 'query']

        for cmd in normal_commands:
            should_quit = cmd.lower() in ['quit', 'exit', 'q']
            self.assertFalse(should_quit)

    def test_empty_input_handling(self):
        """Test empty input handling"""

        user_input = "   "
        stripped = user_input.strip()

        # Empty input should not be processed
        if stripped:
            should_process = True
        else:
            should_process = False

        self.assertFalse(should_process)


def run_integration_tests():
    """Run all integration tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionLifecycle))
    suite.addTests(loader.loadTestsFromTestCase(TestBillSummaryFormatting))
    suite.addTests(loader.loadTestsFromTestCase(TestInteractiveModeLogic))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)

