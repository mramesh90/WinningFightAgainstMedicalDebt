"""
AgentWrapper - Wrapper for Google ADK Agents
Provides a unified interface for Agent, SequentialAgent, and ParallelAgent.
Supports persistent sessions with DatabaseSessionService and Events Compaction.
"""

from google.adk.agents import Agent, ParallelAgent, SequentialAgent, LlmAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from typing import Optional, List, Literal, Any, Dict
import uuid
import logging

logger = logging.getLogger(__name__)


class AgentWrapper:
    """
    Wrapper class for agents (Agent, SequentialAgent, ParallelAgent).
    Provides consistent interface and configuration.
    """

    def __init__(
            self,
            name: str,
            model_name: Optional[str] = None,
            description: Optional[str] = None,
            instruction: Optional[str] = None,
            tools: Optional[List] = None,
            output_key: Optional[str] = None,
            agent_type: Literal["Agent", "ParallelAgent", "SequentialAgent"] = "Agent",
            sub_agents: Optional[List] = None,
            session_service: Optional[Any] = None,
            app_name: Optional[str] = None,
            enable_compaction: bool = False,
            compaction_interval: int = 3,
            overlap_size: int = 1
    ):
        """
        Initialize an agent wrapper.

        Args:
            name: Agent name
            model_name: Model name 
            description: Agent description
            instruction: System instruction for the agent
            tools: List of tools available to the agent
            output_key: Output key for result storage
            agent_type: Type of agent (Agent, ParallelAgent, SequentialAgent)
            sub_agents: List of sub-agents (for ParallelAgent/SequentialAgent)
            session_service: DatabaseSessionService or InMemorySessionService
            app_name: Application name for the runner
            enable_compaction: Enable events compaction
            compaction_interval: Trigger compaction every N invocations
            overlap_size: Keep N previous turns for context
        """
        self.name = name
        self.model_name = model_name
        self.description = description
        self.instruction = instruction
        self.tools = tools if tools is not None else []
        self.output_key = output_key
        self.agent_type = agent_type
        self.sub_agents = sub_agents if sub_agents is not None else []
        self.session_service = session_service
        self.app_name = app_name or "medical_bill_agents"
        self.enable_compaction = enable_compaction
        self.compaction_interval = compaction_interval
        self.overlap_size = overlap_size
        self.agent = None
        self.runner = None
        self.app = None

        if self.agent_type == "Agent":
            if not self.model_name:
                raise ValueError("model_name is required for Agent type")
            self.model = self._create_model()
        else:
            self.model = None

        self._initialize_agent()

    def _create_model(self):
        """Create Gemini model with retry configuration."""
        retry_config = types.HttpRetryOptions(
            attempts=5,
            exp_base=2,
            initial_delay=1,
            http_status_codes=[429, 500, 503, 504]
        )

        safety_settings = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
        ]

        return Gemini(
            model=self.model_name,
            retry_options=retry_config
        )

    def _initialize_agent(self):
        """Initialize the agent with provided configuration based on agent_type."""

        if self.agent_type == "ParallelAgent":
            self.agent = ParallelAgent(
                name=self.name,
                sub_agents=self.sub_agents
            )
            logger.info(f"✅ ParallelAgent '{self.name}' created")

        elif self.agent_type == "SequentialAgent":
            self.agent = SequentialAgent(
                name=self.name,
                sub_agents=self.sub_agents
            )
            logger.info(f"✅ SequentialAgent '{self.name}' created")

        else:  # agent_type == "Agent"
            agent_config = {
                "name": self.name,
                "model": self.model,
                "instruction": self.instruction,
                "tools": self.tools,
            }
            if self.description is not None:
                agent_config["description"] = self.description
            if self.output_key is not None:
                agent_config["output_key"] = self.output_key

            self.agent = Agent(**agent_config)
            logger.info(f"✅ Agent '{self.name}' created")

        # Use InMemoryRunner with run_debug for simple, stateless operations
        self.runner = InMemoryRunner(agent=self.agent, app_name=self.app_name)
        logger.info(f"✅ InMemoryRunner created")

    async def run(self, query, instruction: Optional[str] = None, session_id: Optional[str] = None, user_id: Optional[str] = None):
        """
        Run the agent with the given query.

        Args:
            query: Input query (string or UserContent)
            instruction: Optional instruction override
            session_id: Optional session ID (not used with run_debug)
            user_id: Optional user ID (not used with run_debug)

        Returns:
            Agent response
        """
        if self.runner is None:
            raise RuntimeError("Runner not initialized.")

        # Use run_debug which handles everything automatically
        if isinstance(query, str):
            return await self.runner.run_debug(query)
        elif isinstance(query, types.Content):
            # Extract text from Content object
            if hasattr(query, 'parts') and len(query.parts) > 0:
                text = query.parts[0].text if hasattr(query.parts[0], 'text') else str(query)
            else:
                text = str(query)
            return await self.runner.run_debug(text)
        else:
            return await self.runner.run_debug(str(query))

