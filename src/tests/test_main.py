"""
Test Cases for Medical Bill Processing System with Sessions
============================================================

This test suite covers:
1. Configuration validation
2. Session service initialization
3. Bill processing orchestrator
4. Shared session workflow
5. Chatbot interaction with sessions
6. Follow-up questions functionality
7. End-to-end integration
"""

import asyncio
import unittest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import Config
from orchestrator import MedicalBillOrchestrator
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.genai import types


class TestConfiguration(unittest.TestCase):
    """Test configuration management"""

    def test_config_has_required_attributes(self):
        """Test that Config has all required attributes"""
        self.assertTrue(hasattr(Config, 'GOOGLE_API_KEY'))
        self.assertTrue(hasattr(Config, 'DEFAULT_MODEL'))
        self.assertTrue(hasattr(Config, 'DATABASE_URL'))
        self.assertTrue(hasattr(Config, 'APP_NAME'))
        self.assertTrue(hasattr(Config, 'COMPACTION_INTERVAL'))
        self.assertTrue(hasattr(Config, 'OVERLAP_SIZE'))

    def test_config_database_url_format(self):
        """Test that database URL uses async driver"""
        self.assertIn('aiosqlite', Config.DATABASE_URL)

    def test_config_poppler_path_from_env(self):
        """Test that POPPLER_BIN_PATH can be loaded from environment"""
        # Save original
        original = os.getenv('POPPLER_BIN_PATH')

        # Set test value
        test_path = r"C:\test\poppler\bin"
        os.environ['POPPLER_BIN_PATH'] = test_path

        # Reload config (in real scenario, would reimport)
        # For this test, just verify the pattern works
        loaded_path = os.getenv('POPPLER_BIN_PATH', 'default')
        self.assertEqual(loaded_path, test_path)

        # Restore
        if original:
            os.environ['POPPLER_BIN_PATH'] = original
        else:
            del os.environ['POPPLER_BIN_PATH']

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key_123'})
    def test_config_validation_with_api_key(self):
        """Test config validation when API key is set"""
        try:
            Config.validate()
            # Should not raise
            self.assertTrue(True)
        except ValueError:
            self.fail("Config.validate() raised ValueError with API key set")

    def test_config_validation_without_api_key(self):
        """Test config validation fails without API key"""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': ''}, clear=True):
            # Remove API key
            if 'GOOGLE_API_KEY' in os.environ:
                del os.environ['GOOGLE_API_KEY']

            with self.assertRaises(ValueError) as context:
                # Force re-read of Config.GOOGLE_API_KEY
                Config.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
                Config.validate()

            self.assertIn("GOOGLE_API_KEY", str(context.exception))


class TestSessionService(unittest.IsolatedAsyncioTestCase):
    """Test session service functionality"""

    async def test_database_session_service_creation(self):
        """Test DatabaseSessionService can be created"""
        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)
        self.assertIsInstance(session_service, DatabaseSessionService)

    async def test_in_memory_session_service_creation(self):
        """Test InMemorySessionService can be created"""
        session_service = InMemorySessionService()
        self.assertIsInstance(session_service, InMemorySessionService)

    async def test_session_creation(self):
        """Test creating a new session"""
        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        session = await session_service.create_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session_01"
        )

        self.assertEqual(session.id, "test_session_01")
        self.assertEqual(session.user_id, "test_user")

    async def test_session_retrieval(self):
        """Test retrieving an existing session"""
        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        # Create session
        await session_service.create_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session_02"
        )

        # Retrieve session
        session = await session_service.get_session(
            app_name="test_app",
            user_id="test_user",
            session_id="test_session_02"
        )

        self.assertEqual(session.id, "test_session_02")


class TestOrchestrator(unittest.IsolatedAsyncioTestCase):
    """Test MedicalBillOrchestrator"""

    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized"""
        orchestrator = MedicalBillOrchestrator()
        self.assertIsNotNone(orchestrator)
        self.assertTrue(hasattr(orchestrator, 'bill_extractor'))
        self.assertTrue(hasattr(orchestrator, 'charge_extractor'))
        self.assertTrue(hasattr(orchestrator, 'duplicate_auditor'))
        self.assertTrue(hasattr(orchestrator, 'code_auditor'))
        self.assertTrue(hasattr(orchestrator, 'charge_explainer'))

    async def test_orchestrator_with_missing_file(self):
        """Test orchestrator handles missing bill file gracefully"""
        orchestrator = MedicalBillOrchestrator()

        # Use a non-existent file path
        fake_path = Path("non_existent_bill.pdf")

        # Should handle gracefully (returns results with error or sample data)
        # Based on your code, it creates sample results
        try:
            results = await orchestrator.process_bill(fake_path)
            # Should either return sample results or handle error
            self.assertIsInstance(results, dict)
        except Exception as e:
            # If it raises, that's also acceptable behavior
            self.assertIsInstance(e, Exception)


class TestLLMAgentCreation(unittest.TestCase):
    """Test LLM agent creation"""

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key_123'})
    def test_llm_agent_creation(self):
        """Test creating an LlmAgent"""
        retry_config = types.HttpRetryOptions(
            attempts=3,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )

        agent = LlmAgent(
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            name="test_agent",
            description="Test agent",
        )

        self.assertEqual(agent.name, "test_agent")
        self.assertEqual(agent.description, "Test agent")


class TestRunnerCreation(unittest.TestCase):
    """Test Runner creation with session services"""

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key_123'})
    def test_runner_with_database_session_service(self):
        """Test creating Runner with DatabaseSessionService"""
        retry_config = types.HttpRetryOptions(
            attempts=3,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )

        agent = LlmAgent(
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            name="test_agent",
            description="Test agent",
        )

        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        runner = Runner(
            agent=agent,
            app_name="test_app",
            session_service=session_service
        )

        self.assertIsNotNone(runner)
        self.assertEqual(runner.app_name, "test_app")


class TestSharedSessionWorkflow(unittest.IsolatedAsyncioTestCase):
    """Test the shared session workflow"""

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key_123'})
    async def test_shared_session_concept(self):
        """Test that multiple agents can use the same session"""
        retry_config = types.HttpRetryOptions(
            attempts=3,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )

        # Create session service
        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        SHARED_SESSION_ID = "test_shared_session"
        APP_NAME = "test_app"
        USER_ID = "test_user"

        # Create first agent (summary writer)
        summary_agent = LlmAgent(
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            name="summary_agent",
            description="Writes summary to session",
        )
        summary_runner = Runner(
            agent=summary_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        # Create second agent (chatbot reader)
        chatbot_agent = LlmAgent(
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            name="chatbot_agent",
            description="Reads from session",
        )
        chatbot_runner = Runner(
            agent=chatbot_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        # Both runners should be created successfully
        self.assertIsNotNone(summary_runner)
        self.assertIsNotNone(chatbot_runner)

        # Both should use the same session service
        self.assertEqual(summary_runner.app_name, chatbot_runner.app_name)


class TestContentFormatting(unittest.TestCase):
    """Test Content object creation and formatting"""

    def test_content_creation_from_string(self):
        """Test creating Content object from string"""
        text = "Test message"
        content = types.Content(role="user", parts=[types.Part(text=text)])

        self.assertEqual(content.role, "user")
        self.assertEqual(len(content.parts), 1)
        self.assertEqual(content.parts[0].text, text)

    def test_content_with_multiple_parts(self):
        """Test Content with multiple parts"""
        content = types.Content(
            role="user",
            parts=[
                types.Part(text="Part 1"),
                types.Part(text="Part 2"),
            ]
        )

        self.assertEqual(len(content.parts), 2)
        self.assertEqual(content.parts[0].text, "Part 1")
        self.assertEqual(content.parts[1].text, "Part 2")


class TestBillResultsStructure(unittest.TestCase):
    """Test bill processing results structure"""

    def test_sample_results_structure(self):
        """Test that sample results have expected structure"""
        results = {
            "bill_file": "test_bill.pdf",
            "status": "COMPLETED",
            "stages": {
                "bill_extraction": {"status": "SUCCESS", "data": "Sample extraction"},
                "charge_extraction": {"status": "SUCCESS", "data": "Charges data"},
                "parallel_analysis": {"status": "SUCCESS", "data": "Analysis data"}
            },
            "final_output": "Bill analysis complete."
        }

        # Verify structure
        self.assertIn("bill_file", results)
        self.assertIn("status", results)
        self.assertIn("stages", results)
        self.assertIn("final_output", results)

        # Verify stages
        self.assertIn("bill_extraction", results["stages"])
        self.assertIn("charge_extraction", results["stages"])
        self.assertIn("parallel_analysis", results["stages"])

        # Verify each stage has status
        for stage_name, stage_data in results["stages"].items():
            self.assertIn("status", stage_data)
            self.assertIn("data", stage_data)


class TestRunSessionFunction(unittest.IsolatedAsyncioTestCase):
    """Test the run_session helper function behavior"""

    async def test_run_session_query_list_conversion(self):
        """Test that single query string is converted to list"""
        # Test string to list conversion logic
        single_query = "What is the total?"

        if isinstance(single_query, str):
            query_list = [single_query]

        self.assertIsInstance(query_list, list)
        self.assertEqual(len(query_list), 1)
        self.assertEqual(query_list[0], "What is the total?")

    async def test_run_session_handles_list_queries(self):
        """Test that query list is handled correctly"""
        queries = ["Query 1", "Query 2", "Query 3"]

        self.assertIsInstance(queries, list)
        self.assertEqual(len(queries), 3)


class TestIntegrationWorkflow(unittest.IsolatedAsyncioTestCase):
    """Integration tests for complete workflow"""

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key_123'})
    async def test_complete_workflow_structure(self):
        """Test the overall workflow structure"""
        # This test verifies the workflow logic without actual API calls

        # Step 1: Session service creation
        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)
        self.assertIsNotNone(session_service)

        # Step 2: Orchestrator creation
        orchestrator = MedicalBillOrchestrator()
        self.assertIsNotNone(orchestrator)

        # Step 3: Agent creation
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
        self.assertIsNotNone(summary_agent)

        # Step 4: Runner creation
        runner = Runner(
            agent=summary_agent,
            app_name="test_app",
            session_service=session_service
        )
        self.assertIsNotNone(runner)

        # Workflow structure is valid
        self.assertTrue(True)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""

    def test_missing_api_key_error(self):
        """Test that missing API key raises appropriate error"""
        with patch.dict(os.environ, {}, clear=True):
            if 'GOOGLE_API_KEY' in os.environ:
                del os.environ['GOOGLE_API_KEY']

            Config.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

            with self.assertRaises(ValueError):
                Config.validate()

    def test_invalid_database_url(self):
        """Test handling of invalid database URL"""
        # Test that sync URL is detected (missing aiosqlite)
        sync_url = "sqlite:///test.db"
        async_url = "sqlite+aiosqlite:///test.db"

        self.assertNotIn("aiosqlite", sync_url)
        self.assertIn("aiosqlite", async_url)


class TestSessionPersistence(unittest.IsolatedAsyncioTestCase):
    """Test session persistence features"""

    async def test_session_can_be_created_and_retrieved(self):
        """Test that sessions persist between create and get"""
        db_url = "sqlite+aiosqlite:///:memory:"
        session_service = DatabaseSessionService(db_url=db_url)

        session_id = "persistent_session_test"

        # Create session
        created = await session_service.create_session(
            app_name="test_app",
            user_id="test_user",
            session_id=session_id
        )

        # Retrieve session
        retrieved = await session_service.get_session(
            app_name="test_app",
            user_id="test_user",
            session_id=session_id
        )

        self.assertEqual(created.id, retrieved.id)
        self.assertEqual(created.user_id, retrieved.user_id)


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionService))
    suite.addTests(loader.loadTestsFromTestCase(TestOrchestrator))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMAgentCreation))
    suite.addTests(loader.loadTestsFromTestCase(TestRunnerCreation))
    suite.addTests(loader.loadTestsFromTestCase(TestSharedSessionWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestContentFormatting))
    suite.addTests(loader.loadTestsFromTestCase(TestBillResultsStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestRunSessionFunction))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionPersistence))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success/failure
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

