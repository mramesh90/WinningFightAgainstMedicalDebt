"""
AgentWrapper - Wrapper for Google ADK Agents
Provides a unified interface for Agent, SequentialAgent, and ParallelAgent.
"""

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types
from typing import Optional, List, Literal
import uuid
import logging

logger = logging.getLogger(__name__)


class AgentWrapper:
    """
    Wrapper class for Google ADK agents (Agent, SequentialAgent, ParallelAgent).
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
            sub_agents: Optional[List] = None
    ):
        """
        Initialize an agent wrapper.

        Args:
            name: Agent name
            model_name: Model name (required for Agent type)
            description: Agent description
            instruction: System instruction for the agent
            tools: List of tools available to the agent
            output_key: Output key for result storage
            agent_type: Type of agent (Agent, ParallelAgent, SequentialAgent)
            sub_agents: List of sub-agents (for ParallelAgent/SequentialAgent)
        """
        self.name = name
        self.model_name = model_name
        self.description = description
        self.instruction = instruction
        self.tools = tools if tools is not None else []
        self.output_key = output_key
        self.agent_type = agent_type
        self.sub_agents = sub_agents if sub_agents is not None else []
        self.agent = None
        self.runner = None

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
            retry_options=retry_config,
            safety_settings=safety_settings
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

        self.runner = InMemoryRunner(agent=self.agent, app_name="medical_bill_agents")

    async def run(self, query, instruction: Optional[str] = None):
        """
        Run the agent with the given query.

        Args:
            query: Input query (string or UserContent)
            instruction: Optional instruction override

        Returns:
            Agent response
        """
        if self.runner is None:
            raise RuntimeError("Runner not initialized.")

        # For multimodal inputs
        if isinstance(query, types.UserContent):
            session_id = f"session_{self.name}_{uuid.uuid4().hex[:8]}"
            user_id = "user_default"

            response_generator = self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=query
            )
            final_response = ""
            async for event in response_generator:
                if hasattr(event, 'text'):
                    final_response += event.text
            return final_response
        else:
            # For simple string inputs
            return await self.runner.run_debug(str(query))

