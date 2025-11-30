"""
Conversational Agent Wrapper - For agents that need persistent sessions
Use this for chatbots or agents that need to remember previous conversations.
"""

from google.adk.agents import LlmAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ConversationalAgent:
    """
    Wrapper for conversational agents that maintain session history.
    Perfect for follow-up questions and multi-turn conversations.
    """

    def __init__(
            self,
            name: str,
            model_name: str = "gemini-2.5-flash-lite",
            description: str = "A conversational agent",
            instruction: str = "You are a helpful assistant.",
            enable_compaction: bool = True,
            compaction_interval: int = 3,
            overlap_size: int = 1
    ):
        """
        Initialize a conversational agent.

        Args:
            name: Agent name
            model_name: Model to use
            description: Agent description
            instruction: System instruction
            enable_compaction: Enable events compaction
            compaction_interval: Compact every N turns
            overlap_size: Keep N previous turns
        """
        self.name = name
        self.model_name = model_name
        self.description = description
        self.instruction = instruction

        # Create model with retry
        retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )
        model = Gemini(model=model_name, retry_options=retry_config)

        # Create LlmAgent (simpler than Agent, perfect for conversations)
        self.agent = LlmAgent(
            model=model,
            name=name,
            description=description
        )

        # Create session service (use DatabaseSessionService for persistence)
        # SQLite database will be created automatically
        db_url = "sqlite+aiosqlite:///medical_bill_agent_data.db"
        from google.adk.sessions import DatabaseSessionService
        self.session_service = DatabaseSessionService(db_url=db_url)
        logger.info(f"✅ DatabaseSessionService initialized: {db_url}")

        # Create app with compaction
        if enable_compaction:
            self.app = App(
                name=f"{name}_app",
                root_agent=self.agent,
                events_compaction_config=EventsCompactionConfig(
                    compaction_interval=compaction_interval,
                    overlap_size=overlap_size
                )
            )
            logger.info(f"✅ Conversational agent '{name}' created with compaction")
        else:
            self.app = App(name=f"{name}_app", root_agent=self.agent)
            logger.info(f"✅ Conversational agent '{name}' created")

        # Create runner with session service
        self.runner = Runner(app=self.app, session_service=self.session_service)

        # Store active sessions
        self.sessions = {}  # user_id -> session_id

    async def chat(self, message: str, user_id: str = "default_user", session_id: str = None) -> str:
        """
        Send a message and get a response.
        Automatically maintains session for this user.

        Args:
            message: User's message
            user_id: User identifier (for multi-user support)
            session_id: Optional explicit session ID (if None, auto-generates)

        Returns:
            Agent's response
        """
        # Get or create session for this user
        if session_id is None:
            if user_id not in self.sessions:
                # Create session ID similar to reference example
                self.sessions[user_id] = f"{self.name}_{user_id}_session"
                logger.info(f"📝 Starting new conversation for user: {user_id}")
            session_id = self.sessions[user_id]
        else:
            # Use provided session_id
            self.sessions[user_id] = session_id

        # Convert to Content object
        content = types.Content(role="user", parts=[types.Part(text=message)])

        # Run with session - matching reference pattern
        # Runner.run_async with DatabaseSessionService will auto-create session
        response_generator = self.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        )

        response = ""
        async for event in response_generator:
            if hasattr(event, 'text'):
                response += event.text

        return response

    def reset_session(self, user_id: str = "default_user"):
        """
        Clear the session for a user (start fresh conversation).

        Args:
            user_id: User identifier
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"🔄 Session reset for user: {user_id}")


# Example usage for medical bill follow-up questions
class MedicalBillChatbot(ConversationalAgent):
    """
    Chatbot specifically for answering questions about medical bills.
    Maintains conversation history for follow-up questions.
    """

    def __init__(self):
        super().__init__(
            name="MedicalBillChatbot",
            model_name="gemini-2.5-flash-lite",
            description="A chatbot that answers questions about medical bills",
            instruction=(
                "You are a medical billing expert assistant. "
                "Help users understand their medical bills, explain charges, "
                "identify potential issues, and answer follow-up questions. "
                "Maintain context from previous messages in the conversation. "
                "Be friendly, clear, and patient-focused."
            ),
            enable_compaction=True,
            compaction_interval=5,  # Compact every 5 turns
            overlap_size=2  # Keep 2 previous turns for context
        )


# Example: How to use for follow-up questions
async def example_usage():
    """
    Example showing how to use conversational agents for follow-up questions.
    """
    chatbot = MedicalBillChatbot()

    # First question
    response1 = await chatbot.chat(
        "I see a charge for $500 on my bill. What could that be?",
        user_id="patient_123"
    )
    print(f"Bot: {response1}")

    # Follow-up question - chatbot remembers the $500 charge!
    response2 = await chatbot.chat(
        "Is that amount reasonable?",
        user_id="patient_123"
    )
    print(f"Bot: {response2}")

    # Another follow-up
    response3 = await chatbot.chat(
        "What should I do if I think it's too high?",
        user_id="patient_123"
    )
    print(f"Bot: {response3}")

