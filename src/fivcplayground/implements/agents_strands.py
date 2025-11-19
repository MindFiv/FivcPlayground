"""
Agent implementations for FivcPlayground using Strands framework.

This module provides implementations of IAgent and IAgentProvider interfaces,
enabling flexible agent creation and management through the component architecture.

Classes:
    _AgentRunnable: Strands-based agent execution with IRunnable interface
    AgentImpl: Implementation of IAgent interface for Strands agents
    AgentProviderImpl: Implementation of IAgentProvider interface for agent creation
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, List, Type, cast
from uuid import uuid4

from pydantic import BaseModel
from strands.agent import (
    Agent,
    AgentResult,
    SlidingWindowConversationManager,
)
from strands.models import Model
from strands.types.content import Message, ContentBlock
from strands.types.tools import ToolUse, ToolResult

from fivcglue import IComponentSite
from fivcglue.interfaces.utils import query_component

from fivcplayground.interfaces import (
    IAgent,
    IAgentProvider,
    IModelProvider,
    IToolProvider,
    ISettingProvider,
    AgentConfig,
    IRunnableCallback,
    IRunnableSession,
    IRunnable,
    RunnableTrace,
    RunnableStatus,
    RunnableContent,
    RunnableTraceToolCall,
)
from fivcplayground.legacies.tools import setup_tools, Tool

logger = logging.getLogger(__name__)


class _NullCallback(IRunnableCallback):
    """No-op callback implementation for when no callback is provided."""

    def on_start(self, trace: RunnableTrace) -> None:
        """No-op on_start."""
        pass

    def on_finish(self, trace: RunnableTrace) -> None:
        """No-op on_finish."""
        pass

    def on_update(self, trace: RunnableTrace) -> None:
        """No-op on_update."""
        pass

    def on_tool(self, trace: RunnableTrace) -> None:
        """No-op on_tool."""
        pass

    def on_delta(self, trace: RunnableTrace) -> None:
        """No-op on_delta."""
        pass


NULL_CALLBACK = _NullCallback()


class _AgentRunnable(IRunnable):
    """
    Strands-based agent execution with IRunnable interface.

    This class implements agent execution using the Strands framework,
    providing streaming execution with tool support, callbacks, and
    session management.

    Example:
        >>> agent_runnable = _AgentRunnable(
        ...     model=model,
        ...     tools=[tool1, tool2],
        ...     agent_id="agent-1",
        ...     agent_name="Assistant",
        ...     system_prompt="You are a helpful assistant"
        ... )
        >>> trace = agent_runnable.run("What is 2+2?")
        >>> print(trace.status)
        RunnableStatus.COMPLETED
    """

    def __init__(
        self,
        model: Model,
        tools: List[Tool] | None = None,
        agent_id: str | None = None,
        agent_name: str = "Default",
        system_prompt: str | None = None,
        response_model: Type[BaseModel] | None = None,
        callback: IRunnableCallback | None = None,
        session: IRunnableSession | None = None,
        **kwargs: Any,
    ):
        """Initialize _AgentRunnable.

        Args:
            model: The Strands Model to use
            tools: List of tools available to the agent
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name for the agent
            system_prompt: System prompt for the agent
            response_model: Optional Pydantic model for structured output
            callback: Optional callback for execution events
            session: Optional session for trace management
            **kwargs: Additional arguments
        """
        self._id = agent_id or str(uuid4())
        self._name = agent_name
        self._model = model
        self._tools = tools or []
        self._system_prompt = system_prompt
        self._response_model = response_model
        self._callback = callback or NULL_CALLBACK
        self._session = session
        self._messages: List[Message] = []

    @property
    def id(self) -> str:
        """Get the runnable ID."""
        return self._id

    @property
    def name(self) -> str:
        """Get the runnable name."""
        return self._name

    def run(
        self,
        query: str | RunnableContent = "",
        **kwargs: Any,
    ) -> RunnableTrace:
        """Execute the agent synchronously.

        Args:
            query: The user query to process
            **kwargs: Additional arguments

        Returns:
            RunnableTrace with execution results
        """
        return asyncio.run(self.run_async(query, **kwargs))

    async def run_async(
        self,
        query: str | RunnableContent = "",
        **kwargs: Any,
    ) -> RunnableTrace:
        """Execute the agent asynchronously.

        Args:
            query: The user query to process
            **kwargs: Additional arguments

        Returns:
            RunnableTrace with execution results
        """
        # Convert query to RunnableContent if needed
        query_str = query.text if isinstance(query, RunnableContent) else str(query)

        trace = RunnableTrace(
            id=str(uuid4()),
            status=RunnableStatus.EXECUTING,
            query=RunnableContent(text=query_str) if query_str else None,
            started_at=datetime.now(),
        )

        self._callback.on_start(trace)

        try:
            # Add user message to conversation
            if query_str:
                self._messages.append(
                    Message(role="user", content=[ContentBlock(text=query_str)])
                )

            # Setup tools and execute agent
            async with setup_tools(self._tools) as tools_expanded:
                agent = Agent(
                    agent_id=self._id,
                    model=self._model,
                    tools=tools_expanded,
                    name=self._name,
                    system_prompt=self._system_prompt,
                    conversation_manager=SlidingWindowConversationManager(
                        window_size=10
                    ),
                )

                output = None
                async for event_data in agent.stream_async(
                    prompt=self._messages,
                    structured_output_model=self._response_model,
                ):
                    if "result" in event_data:
                        output = event_data["result"]

                    elif "data" in event_data:
                        # Streaming text data
                        text_chunk = event_data["data"]
                        current_text = trace.reply.text if trace.reply else ""
                        trace.reply = RunnableContent(text=current_text + text_chunk)
                        self._callback.on_delta(trace)

                    elif "message" in event_data:
                        # Message update with potential tool calls
                        message = event_data["message"]
                        for block in message.get("content", []):
                            if "toolUse" in block:
                                tool_use = cast(ToolUse, block["toolUse"])
                                tool_use_id = tool_use.get("toolUseId")
                                tool_call = RunnableTraceToolCall(
                                    id=tool_use_id,
                                    name=tool_use.get("name"),
                                    input=tool_use.get("input"),
                                    status=RunnableStatus.EXECUTING,
                                )
                                trace.tool_calls[tool_use_id] = tool_call
                                self._callback.on_tool(trace)

                            elif "toolResult" in block:
                                tool_result = cast(ToolResult, block["toolResult"])
                                tool_use_id = tool_result.get("toolUseId")
                                # Find and update the tool call
                                if tool_use_id in trace.tool_calls:
                                    tc = trace.tool_calls[tool_use_id]
                                    tc.status = RunnableStatus.COMPLETED
                                    tc.output = tool_result.get("content")

                if not isinstance(output, AgentResult):
                    raise ValueError(f"Expected AgentResult, got {type(output)}")

                # Add assistant message to conversation
                self._messages.append(output.message)

                # Set reply content
                trace.reply = RunnableContent(text=str(output))
                trace.status = RunnableStatus.COMPLETED

        except Exception as e:
            logger.exception(f"Error executing agent: {e}")
            trace.status = RunnableStatus.FAILED
            trace.reply = RunnableContent(text=f"Error: {str(e)}")
            self._callback.on_finish(trace)
            raise

        finally:
            trace.completed_at = datetime.now()

        self._callback.on_finish(trace)

        if self._session:
            self._session.set_trace(trace)

        return trace


class AgentImpl(IAgent):
    """
    Implementation of IAgent interface with lazy loading support.

    This class represents a single agent instance with metadata and lazy-loaded
    access to the underlying agent runnable. The actual runnable instantiation
    is deferred until get_runnable() is first called.

    Example:
        >>> config = AgentConfig(
        ...     model="default_llm",
        ...     description="A helpful assistant",
        ...     system_prompt="You are helpful."
        ... )
        >>> agent = AgentImpl("agent_1", "Assistant", config)
        >>> runnable = agent.get_runnable("What is 2+2?")
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        config: AgentConfig,
        model_provider: IModelProvider | None = None,
        tool_provider: IToolProvider | None = None,
        user_id: str | None = None,
    ):
        """
        Initialize an agent instance.

        Args:
            agent_id: Unique identifier for the agent
            name: Name of the agent
            description: Description of the agent
            config: AgentConfig with model, description, and system_prompt
            model_provider: Optional IModelProvider for resolving models
            tool_provider: Optional IToolProvider for resolving tools
            user_id: Optional user ID for multi-user support (isolates user data)
        """
        self._agent_id = agent_id
        self._name = name
        self._description = description
        self._config = config
        self._model_provider = model_provider
        self._tool_provider = tool_provider
        self._user_id = user_id
        self._runnable_cache = {}  # Cache runnables by query

    @property
    def id(self) -> str:
        """Get the agent ID."""
        return self._agent_id

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self._name

    @property
    def description(self) -> str:
        """Get the agent description."""
        return self._description

    @property
    def config(self) -> AgentConfig:
        """Get the agent configuration."""
        return self._config

    def get_runnable(
        self,
        query: str,
        callback: IRunnableCallback | None = None,
        session: IRunnableSession | None = None,
        **kwargs: Any,
    ) -> IRunnable:
        """
        Get the runnable for the agent.

        Creates a new _AgentRunnable instance with the agent's model and tools.

        Args:
            query: The query to execute
            callback: Optional callback for execution events
            session: Optional session for trace management
            **kwargs: Additional parameters

        Returns:
            An IRunnable instance ready for execution
        """
        # Resolve model
        model = None
        if self._model_provider:
            model_impl = self._model_provider.get_model(
                self._config.model, user_id=self._user_id
            )
            if model_impl:
                model = model_impl.get_underlying()

        # Resolve tools
        tools = []
        if self._tool_provider:
            for tool in self._tool_provider.search_tools(query, user_id=self._user_id):
                tools.append(tool)

        # Create agent runnable with Strands framework
        return _AgentRunnable(
            model=model,
            tools=tools,
            agent_id=self._agent_id,
            agent_name=self._name,
            system_prompt=self._config.system_prompt,
            response_model=kwargs.get("response_model"),
            callback=callback,
            session=session,
        )


class AgentProviderImpl(IAgentProvider):
    """
    Implementation of IAgentProvider interface for agent creation and management.

    This class provides access to agent instances configured in settings.
    Each setting represents an agent configuration with model, description,
    and system_prompt. The provider creates AgentImpl instances that wrap
    the legacy agent system.

    Example:
        >>> from fivcplayground.settings import default_component_site
        >>> from fivcplayground.interfaces import IAgentProvider
        >>> provider = default_component_site.get_component(IAgentProvider)
        >>> agent = provider.get_agent("assistant")
        >>> if agent:
        ...     print(f"Agent: {agent.name}")

    Configuration file example (settings.yaml):
        agents:
          assistant:
            model: default_llm
            description: A helpful assistant
            system_prompt: You are a helpful assistant.
          consultant:
            model: reasoning_llm
            description: A task assessment specialist
            system_prompt: You are a consultant.
    """

    def __init__(self, component_site: IComponentSite, **kwargs: Any):
        """
        Initialize the agent provider.

        Args:
            component_site: An IComponentSite instance for component registration
            **kwargs: Additional keyword arguments (unused, for compatibility)
        """
        self._agents_cache = {}  # Cache for created agents
        self._component_site = component_site
        # Try to get named setting provider first, fall back to default
        self._setting_provider = query_component(
            component_site, ISettingProvider, "agents"
        )
        if self._setting_provider is None:
            self._setting_provider = query_component(component_site, ISettingProvider)
        self._model_provider = query_component(component_site, IModelProvider)
        self._tool_provider = query_component(component_site, IToolProvider)

    def get_agent(
        self,
        name: str,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> IAgent | None:
        """
        Get an agent instance by name.

        Retrieves the agent configuration from settings and returns an AgentImpl
        instance. AgentImpl instances are cached to avoid redundant configuration
        lookups.

        Args:
            name: Name of the agent to retrieve (e.g., "assistant", "consultant")
            user_id: Optional user ID for multi-user support (isolates user data)
            **kwargs: Additional configuration parameters (overrides settings)

        Returns:
            An AgentImpl instance if the agent exists, None otherwise.
            Returns None if the agent name is not found in settings.

        Raises:
            ValueError: If invalid configuration values are encountered
        """
        # Check cache first
        cache_key = f"{name}:{user_id}" if user_id else name
        if cache_key in self._agents_cache:
            return self._agents_cache[cache_key]

        # Get agent configuration from settings
        setting = self._setting_provider.get_setting(name, user_id)
        if setting is None:
            return None

        # Build configuration from setting
        config_dict = {}
        for key, value in setting.list():
            config_dict[key] = value

        # Override with any provided kwargs
        config_dict.update(kwargs)

        try:
            # Create AgentConfig
            agent_config = AgentConfig(**config_dict)

            # Create AgentImpl
            agent = AgentImpl(
                agent_id=str(uuid4()),
                name=name,
                description=agent_config.description,
                config=agent_config,
                model_provider=self._model_provider,
                tool_provider=self._tool_provider,
                user_id=user_id,
            )

            # Cache the agent
            self._agents_cache[cache_key] = agent

            return agent

        except (ValueError, TypeError, AttributeError) as e:
            logger.error(f"Failed to create agent '{name}': {e}")
            return None

    def list_agents(
        self,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> List[IAgent]:
        """
        List all available agents.

        Iterates through all agent settings and attempts to create agent instances
        for each one. Agents that fail to create are skipped.

        Args:
            user_id: Optional user ID for multi-user support (isolates user data)
            **kwargs: Additional configuration parameters

        Returns:
            A list of AgentImpl instances for all successfully created agents.
        """
        agents = []
        for setting in self._setting_provider.list_settings(user_id, **kwargs):
            agent = self.get_agent(setting.name, user_id, **kwargs)
            if agent is not None:
                agents.append(agent)
        return agents
