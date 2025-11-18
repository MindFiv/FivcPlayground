"""
Chat utility for handling conversation state and agent execution.

This module provides the Chat class to replace the old ChatSession,
with a cleaner interface and support for agent runtime persistence.

The Chat class manages:
- Agent conversation state and history
- Agent execution with streaming support
- Runtime persistence via AgentsRuntimeRepository
- Agent metadata management

Example:
    >>> from fivcplayground.app.utils import Chat
    >>> from fivcplayground import tools
    >>> from fivcplayground.agents.types.repositories import FileAgentsRuntimeRepository
    >>> from fivcplayground.utils import OutputDir
    >>>
    >>> # Create chat with custom repository
    >>> repo = FileAgentsRuntimeRepository(output_dir=OutputDir("./my_agents"))
    >>> chat = Chat(
    ...     agent_runtime_repo=repo,
    ...     tools_retriever=tools.default_retriever
    ... )
    >>>
    >>> # Or use default repository
    >>> chat = Chat(tools_retriever=tools.default_retriever)
    >>>
    >>> # Send a query
    >>> result = await chat.ask_async("What is the weather?")
    >>>
    >>> # List conversation history
    >>> history = chat.list_history()
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Callable, List

from langchain_core.messages import BaseMessage
from pydantic import BaseModel

from fivcplayground import agents, tools
from fivcplayground.tasks import create_briefing_task
from fivcplayground.agents.types import (
    AgentsRuntime,
    AgentsMonitorManager,
    AgentsRuntimeMeta,
)
from fivcplayground.agents.types.repositories import (
    AgentsRuntimeRepository,
    SqliteAgentsRuntimeRepository,
)
from fivcplayground.utils import OutputDir


class Chat(object):
    """
    Manages chat conversation state and agent execution.

    This is a complete rewrite of ChatSession with a cleaner interface,
    improved separation of concerns, and built-in support for agent
    runtime persistence.

    The Chat class handles:
    - Creating and managing a unique agent instance
    - Executing queries with streaming support
    - Persisting agent metadata and runtime history
    - Loading conversation history from previous sessions

    Attributes:
        tools_retriever: Retriever for tool access
        runtime_meta: Agent metadata (agent_id, name, system_prompt, description)
        runtime_repo: Repository for persisting agent runtime state
        monitor_manager: Manager for creating and monitoring agent executions
        running: Boolean flag indicating if agent is currently processing

    Properties:
        id: The unique agent identifier (from runtime_meta.id)
        description: The chat description (from runtime_meta.description or id)
        is_running: Whether the agent is currently processing a query

    Example:
        >>> from fivcplayground.app.utils import Chat
        >>> from fivcplayground import tools
        >>>
        >>> # Create new chat instance
        >>> chat = Chat(tools_retriever=tools.default_retriever)
        >>>
        >>> # Send query with streaming callback
        >>> async def handle_stream(runtime):
        ...     print(f"Streaming: {runtime.streaming_text}")
        >>>
        >>> result = await chat.ask_async(
        ...     "What is 2+2?",
        ...     on_event=handle_stream
        ... )
        >>>
        >>> # Access chat properties
        >>> print(f"Chat ID: {chat.id}")
        >>> print(f"Description: {chat.description}")
        >>>
        >>> # Get conversation history
        >>> for runtime in chat.list_history():
        ...     print(f"Q: {runtime.query}")
        ...     print(f"A: {runtime.reply}")
        >>>
        >>> # Clear history and start fresh
        >>> chat.cleanup()

    Note:
        - Agent metadata is auto-generated on first query if not provided
        - Agent metadata (name, system_prompt) is automatically saved on first query
        - Only completed runtimes are included in history
        - The default repository stores data in OutputDir().subdir("agents")
        - Use ChatManager to manage multiple chat instances
    """

    def __init__(
        self,
        agent_runtime_meta: Optional[AgentsRuntimeMeta] = None,
        agent_runtime_repo: Optional[AgentsRuntimeRepository] = None,
        tools_retriever: Optional[tools.ToolsRetriever] = None,
    ):
        """
        Initialize Chat manager.

        Creates a new chat instance with agent runtime tracking and persistence.
        If no repository is provided, a default FileAgentsRuntimeRepository is
        created in the standard output directory.

        Args:
            agent_runtime_meta: Optional agent metadata containing agent_id, agent_name,
                               system_prompt, and description. If not provided, a new
                               agent will be created on the first query with auto-generated
                               metadata. Use this to resume a previous chat session.
            agent_runtime_repo: Optional repository for persisting agent runtime state.
                               If not provided, defaults to FileAgentsRuntimeRepository
                               with OutputDir().subdir("agents").
            tools_retriever: Retriever for tool access. Required parameter that
                            provides tools to the agent based on the query.

        Raises:
            AssertionError: If tools_retriever is None

        Example:
            >>> from fivcplayground.app.utils import Chat
            >>> from fivcplayground import tools
            >>>
            >>> # Create new chat with default repository
            >>> chat = Chat(tools_retriever=tools.default_retriever)
            >>>
            >>> # Resume existing chat with metadata
            >>> from fivcplayground.agents.types import AgentsRuntimeMeta
            >>> meta = AgentsRuntimeMeta(
            ...     agent_id="my-agent-123",
            ...     agent_name="My Assistant",
            ...     system_prompt="You are a helpful assistant",
            ...     description="Customer support bot"
            ... )
            >>> chat = Chat(
            ...     agent_runtime_meta=meta,
            ...     tools_retriever=tools.default_retriever
            ... )
            >>>
            >>> # Create with custom repository
            >>> from fivcplayground.agents.types.repositories import FileAgentsRuntimeRepository
            >>> from fivcplayground.utils import OutputDir
            >>>
            >>> repo = FileAgentsRuntimeRepository(
            ...     output_dir=OutputDir("./custom_agents")
            ... )
            >>> chat = Chat(
            ...     agent_runtime_repo=repo,
            ...     tools_retriever=tools.default_retriever
            ... )

        Note:
            - The tools_retriever is required and must not be None
            - The agent_runtime_repo defaults to a file-based repository if not provided
            - If agent_runtime_meta is None, metadata is auto-created on first query
        """
        from fivcplayground.agents.types.repositories import FileAgentsRuntimeRepository
        from fivcplayground.utils import OutputDir

        assert tools_retriever is not None, "tools_retriever is required"

        # Create default repository if not provided
        if agent_runtime_repo is None:
            agent_runtime_repo = FileAgentsRuntimeRepository(
                output_dir=OutputDir().subdir("agents")
            )

        self.tools_retriever = tools_retriever
        self.runtime_meta = agent_runtime_meta
        self.runtime_repo = agent_runtime_repo
        self.monitor_manager = AgentsMonitorManager(
            runtime_repo=self.runtime_repo,
        )
        self.running = False

    @property
    def id(self):
        """
        Get the unique identifier for this chat's agent.

        Returns the agent_id from the runtime metadata if available,
        otherwise returns None for new chats that haven't been initialized yet.

        Returns:
            str | None: The agent ID, or None if no metadata exists yet

        Example:
            >>> chat = Chat(tools_retriever=tools.default_retriever)
            >>> print(chat.id)  # None (not initialized yet)
            >>> await chat.ask("Hello")
            >>> print(chat.id)  # UUID string like "abc-123-def-456"
        """
        return self.runtime_meta.id if self.runtime_meta else None

    @property
    def description(self):
        """
        Get the description for this chat.

        Returns the description from runtime metadata if available,
        otherwise falls back to the agent ID. Returns empty string
        if no metadata exists.

        Returns:
            str: The chat description, agent ID, or empty string

        Example:
            >>> from fivcplayground.agents.types import AgentsRuntimeMeta
            >>> meta = AgentsRuntimeMeta(
            ...     agent_id="my-agent",
            ...     description="Customer support bot"
            ... )
            >>> chat = Chat(
            ...     agent_runtime_meta=meta,
            ...     tools_retriever=tools.default_retriever
            ... )
            >>> print(chat.description)  # "Customer support bot"
        """
        return (
            (self.runtime_meta.description or self.runtime_meta.id)
            if self.runtime_meta
            else ""
        )

    @property
    def started_at(self):
        return self.runtime_meta.started_at if self.runtime_meta else None

    @property
    def is_running(self):
        """
        Check if the agent is currently processing a query.

        This property reflects the internal running state, which is set to True
        when ask() is called and reset to False when execution completes or fails.

        Returns:
            bool: True if agent is currently executing a query, False otherwise

        Example:
            >>> chat = Chat(tools_retriever=tools.default_retriever)
            >>> print(chat.is_running)
            False
            >>> # During async execution, is_running would be True
        """
        return self.running

    def list_history(self) -> List[AgentsRuntime]:
        """
        List all completed agent runtimes for this chat session.

        Retrieves all agent runtimes associated with this chat's agent_id
        and filters to return only those that have completed (successfully
        or with failure). Pending or executing runtimes are excluded.

        Returns:
            List[AgentsRuntime]: List of completed agent runtime instances,
                                sorted chronologically by agent_run_id.
                                Returns empty list if no completed runtimes exist.

        Example:
            >>> chat = Chat(tools_retriever=tools.default_retriever)
            >>> await chat.ask_async("What is 2+2?")
            >>> await chat.ask_async("What is 3+3?")
            >>>
            >>> # Get all completed conversations
            >>> history = chat.list_history()
            >>> for runtime in history:
            ...     print(f"Q: {runtime.query}")
            ...     if runtime.reply:
            ...         print(f"A: {runtime.reply['content'][0]['text']}")

        Note:
            - Only runtimes with status COMPLETED or FAILED are included
            - Runtimes are loaded from the repository each time this is called
            - Tool calls are loaded separately for each runtime
        """
        if not self.runtime_meta:
            return []

        agent_runtimes = self.runtime_repo.list_agent_runtimes(
            self.runtime_meta.agent_id,
        )
        # Filter to only completed runtimes
        completed_agent_runtimes = []
        for runtime in agent_runtimes:
            if not runtime.is_completed:
                continue

            # Load tool calls for completed runtimes
            runtime_tool_calls = self.runtime_repo.list_agent_runtime_tool_calls(
                self.runtime_meta.agent_id, runtime.agent_run_id
            )
            runtime_tool_calls.sort(key=lambda tc: tc.started_at)
            runtime.tool_calls = {tc.tool_use_id: tc for tc in runtime_tool_calls}
            completed_agent_runtimes.append(runtime)
        return completed_agent_runtimes

    async def ask_async(
        self,
        query: str,
        on_event: Optional[Callable[[AgentsRuntime], None]] = None,
    ) -> BaseMessage | BaseModel:
        """
        Send a query to the agent and get a response.

        Executes the agent with the provided query, optionally streaming
        intermediate results via the on_event callback. The agent's response
        is automatically persisted to the repository along with all tool calls
        and execution metadata.

        On the first query, the agent's metadata (name and system_prompt) is
        automatically saved to the repository for future reference.

        Args:
            query: User query string to send to the agent
            on_event: Optional callback function invoked during agent execution.
                     Receives AgentsRuntime instance with updated state including:
                     - streaming_text: Accumulated text as it's generated
                     - tool_calls: Dictionary of tool calls made so far
                     - status: Current execution status
                     The callback is called after each streaming chunk and tool call.

        Returns:
            AgentResult: The final result from the agent execution, containing
                        the complete response message and any tool results.

        Raises:
            ValueError: If the agent is already processing a query (running=True).
                       Only one query can be processed at a time per Chat instance.

        Example:
            >>> from fivcplayground.app.utils import Chat
            >>> from fivcplayground import tools
            >>>
            >>> chat = Chat(tools_retriever=tools.default_retriever)
            >>>
            >>> # Simple query without streaming
            >>> result = await chat.ask_async("What is the capital of France?")
            >>> print(result.message)
            >>>
            >>> # Query with streaming callback
            >>> def on_stream(runtime):
            ...     print(f"Streaming: {runtime.streaming_text}")
            ...     for tool_call in runtime.tool_calls.values():
            ...         print(f"Tool: {tool_call.tool_name}")
            >>>
            >>> result = await chat.ask_async(
            ...     "Search for Python tutorials",
            ...     on_event=on_stream
            ... )

        Note:
            - The running flag is automatically managed (set/reset)
            - Agent metadata is saved on first query if not already present
            - All execution state is persisted to the repository
            - The on_event callback receives the complete runtime state
            - Previous conversation history is automatically loaded for context
        """
        if self.running:
            raise ValueError("Agent is already processing a query")

        try:
            # Set running flag
            self.running = True

            # Load agent metadata if exists
            if self.runtime_meta:
                agent_runtimes = self.runtime_repo.list_agent_runtimes(
                    self.runtime_meta.agent_id
                )
                agent_kwargs = {
                    "agent_id": self.runtime_meta.agent_id,
                    "name": self.runtime_meta.agent_name,
                    "system_prompt": self.runtime_meta.system_prompt,
                    "messages": agent_runtimes,
                }
            else:
                agent_kwargs = {}

            # Filter out None values
            agent_kwargs = {k: v for k, v in agent_kwargs.items() if v}
            agent_creator = agents.default_retriever.get("Companion")
            agent_tools = self.tools_retriever.retrieve(query)
            agent_monitor = self.monitor_manager.create_agent_runtime(on_event=on_event)
            agent = agent_creator(
                callback_handler=agent_monitor,
                tools=agent_tools,
                **agent_kwargs,
            )
            # Execute agent
            agent_result = await agent.run_async(query)

            # Save agent metadata on first query
            if not self.runtime_meta:
                agent_query = f"{query}\n{str(agent_result)}"
                agent_desc = create_briefing_task(
                    agent_query,
                    tools_retriever=self.tools_retriever,
                )
                agent_desc = await agent_desc.run_async()
                self.runtime_meta = AgentsRuntimeMeta(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    system_prompt=agent.system_prompt,
                    description=agent_desc.text,
                    started_at=datetime.now(),
                )
                self.runtime_repo.update_agent(self.runtime_meta)

            return agent_result

        finally:
            # Always reset running flag
            self.running = False

    def ask(
        self,
        query: str,
        on_event: Optional[Callable[[AgentsRuntime], None]] = None,
    ) -> BaseMessage | BaseModel:
        return asyncio.run(self.ask_async(query, on_event))

    def cleanup(self) -> None:
        """
        Clear conversation history and delete all agent data.

        Deletes the agent and all associated runtimes from the repository.
        This includes:
        - Agent metadata (agent.json)
        - All agent runtimes (run_*/run.json)
        - All tool calls (run_*/tool_calls/*.json)

        After cleanup, the agent_id remains the same, but all history is lost.
        The next query will create a new agent with fresh metadata.

        Example:
            >>> chat = Chat(tools_retriever=tools.default_retriever)
            >>> await chat.ask("Hello")
            >>> await chat.ask("How are you?")
            >>>
            >>> # Check history
            >>> print(len(chat.list_history()))  # 2
            >>>
            >>> # Clear everything
            >>> chat.cleanup()
            >>> print(len(chat.list_history()))  # 0

        Note:
            - This is a destructive operation that cannot be undone
            - The agent_id is not changed, only the data is deleted
            - Use this to start a completely fresh conversation
            - The repository's delete_agent() handles cascading deletes
        """
        if self.runtime_meta:
            self.runtime_repo.delete_agent(self.runtime_meta.id)


class ChatManager(object):
    """
    Manages multiple chat instances with shared repository and tools.

    ChatManager provides a centralized way to create and manage multiple
    Chat instances, all sharing the same repository and tools retriever.
    This is useful for applications that need to handle multiple concurrent
    chat sessions or provide a chat list interface.

    Attributes:
        runtime_repo: Repository for persisting agent runtime state
        tools_retriever: Retriever for tool access

    Example:
        >>> from fivcplayground.app.utils import ChatManager
        >>> from fivcplayground import tools
        >>>
        >>> # Create manager with default settings
        >>> manager = ChatManager()
        >>>
        >>> # List all existing chats
        >>> chats = manager.list_chats()
        >>> for chat in chats:
        ...     print(f"{chat.id}: {chat.description}")
        >>>
        >>> # Create a new chat
        >>> new_chat = manager.add_chat()
        >>> await new_chat.ask_async("Hello!")
        >>>
        >>> # Create manager with custom repository
        >>> from fivcplayground.agents.types.repositories import FileAgentsRuntimeRepository
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> repo = FileAgentsRuntimeRepository(
        ...     output_dir=OutputDir("./my_chats")
        ... )
        >>> manager = ChatManager(
        ...     agent_runtime_repo=repo,
        ...     tools_retriever=tools.default_retriever
        ... )

    Note:
        - All chats created by this manager share the same repository
        - All chats use the same tools retriever
        - The manager loads existing chats from the repository
    """

    def __init__(
        self,
        agent_runtime_repo: Optional[AgentsRuntimeRepository] = None,
        tools_retriever: Optional[tools.ToolsRetriever] = None,
    ):
        """
        Initialize ChatManager.

        Creates a manager for handling multiple chat instances with
        shared repository and tools configuration.

        Args:
            agent_runtime_repo: Optional repository for persisting agent runtime state.
                               If not provided, defaults to FileAgentsRuntimeRepository
                               with OutputDir().subdir("agents").
            tools_retriever: Optional retriever for tool access. If not provided,
                            defaults to tools.default_retriever.

        Example:
            >>> from fivcplayground.app.utils import ChatManager
            >>>
            >>> # Create with defaults
            >>> manager = ChatManager()
            >>>
            >>> # Create with custom settings
            >>> from fivcplayground import tools
            >>> from fivcplayground.agents.types.repositories import FileAgentsRuntimeRepository
            >>> from fivcplayground.utils import OutputDir
            >>>
            >>> manager = ChatManager(
            ...     agent_runtime_repo=FileAgentsRuntimeRepository(
            ...         output_dir=OutputDir("./chats")
            ...     ),
            ...     tools_retriever=tools.default_retriever
            ... )
        """
        self.runtime_repo = agent_runtime_repo or SqliteAgentsRuntimeRepository(
            str(OutputDir().subdir("agents"))
        )
        self.tools_retriever = tools_retriever or tools.default_retriever

    def list_chats(self) -> List[Chat]:
        """
        List all existing chat instances.

        Retrieves all agent metadata from the repository and creates
        Chat instances for each one. This allows you to access all
        previously created chats and their conversation history.

        Returns:
            List[Chat]: List of Chat instances, one for each agent in the repository.
                       Returns empty list if no agents exist.

        Example:
            >>> manager = ChatManager()
            >>>
            >>> # Create some chats
            >>> chat1 = manager.add_chat()
            >>> await chat1.ask_async("Hello")
            >>> chat2 = manager.add_chat()
            >>> await chat2.ask_async("Hi there")
            >>>
            >>> # List all chats
            >>> all_chats = manager.list_chats()
            >>> print(f"Total chats: {len(all_chats)}")
            >>>
            >>> # Access chat details
            >>> for chat in all_chats:
            ...     print(f"Chat {chat.id}: {chat.description}")
            ...     history = chat.list_history()
            ...     print(f"  Messages: {len(history)}")

        Note:
            - Each Chat instance shares the same repository and tools
            - The chats are loaded fresh from the repository each time
            - Changes to one chat are persisted and visible to others
        """
        chats = [
            Chat(
                agent_runtime_repo=self.runtime_repo,
                tools_retriever=self.tools_retriever,
                agent_runtime_meta=runtime_meta,
            )
            for runtime_meta in self.runtime_repo.list_agents()
        ]
        # Sort by started_at, treating None as the earliest time (datetime.min)
        chats.sort(
            key=lambda chat: chat.started_at
            or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        return chats

    def add_chat(self) -> Chat:
        """
        Create a new chat instance.

        Creates and returns a new Chat instance with no existing metadata.
        The chat will auto-generate its agent_id and metadata on the first
        query. The new chat uses the manager's shared repository and tools.

        Returns:
            Chat: A new Chat instance ready to use

        Example:
            >>> manager = ChatManager()
            >>>
            >>> # Create a new chat
            >>> chat = manager.add_chat()
            >>> print(chat.id)  # None (not initialized yet)
            >>>
            >>> # Use the chat
            >>> await chat.ask("What is Python?")
            >>> print(chat.id)  # Now has a UUID
            >>>
            >>> # The chat is now in the list
            >>> all_chats = manager.list_chats()
            >>> print(len(all_chats))  # Includes the new chat

        Note:
            - The new chat has no metadata until the first query
            - The chat is automatically persisted on first use
            - Multiple calls create independent chat instances
        """
        return Chat(
            agent_runtime_repo=self.runtime_repo,
            tools_retriever=self.tools_retriever,
        )
