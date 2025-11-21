"""
Agent execution monitor for tracking single-agent execution.

This module provides monitoring and management classes for agent execution:

Core Classes:
    - AgentMonitor: Tracks single agent execution through callback events
    - AgentMonitorManager: Manages multiple agent executions with persistence

Features:
    - Real-time streaming text accumulation
    - Tool call event capture with status tracking
    - Unified callback pattern for execution events
    - Framework-agnostic design (no UI dependencies)
    - Graceful error handling for callbacks
    - Automatic persistence via AgentRunRepository
    - Conversation history management
    - Multi-turn agent support

Callback Pattern:
    The monitor uses a unified callback pattern where a single on_event callback
    receives the complete AgentRun state after each event, allowing UI
    components to access all execution data in one place.

Integration with AgentRunnable:
    AgentMonitor integrates with AgentRunnable through callback_handler parameter,
    capturing execution events and maintaining runtime state. The monitor receives
    string responses from AgentRunnable and stores them in the runtime.

Key Features:
    - Unified callback-based execution tracking via AgentRun
    - Real-time streaming message accumulation
    - Tool call event capture with status tracking
    - Framework-agnostic design (no UI dependencies)
    - Graceful error handling for callbacks
    - Cleanup method for resetting state between executions
    - Centralized agent lifecycle management through AgentMonitorManager
    - Automatic agent creation with monitoring integration
"""

from typing import Optional, List, Callable

from fivcplayground.agents.types.base import (
    AgentRunStatus,
    AgentRunEvent,
    AgentRun,
    AgentRunToolCall,
)
from fivcplayground.agents.types.repositories import (
    AgentRunRepository,
)


class AgentMonitor(object):
    """
    Agent execution monitor for tracking single-agent execution.

    Tracks agent execution through callback events, capturing streaming text
    chunks and execution state in an AgentRun object. Provides real-time
    callbacks for UI updates while maintaining framework-agnostic design.

    Integration with Runnable:
    The monitor is passed as callback_handler to Runnable and receives
    execution events through the __call__ method with different modes:
    - "start": Execution started
    - "messages": Streaming message chunks
    - "values": Final output values (including structured_response or messages)
    - "updates": State updates
    - "finish": Execution completed

    All events are accumulated in an AgentRun object that tracks:
    - Streaming text accumulation
    - Tool call execution with status tracking
    - Overall execution status
    - Final reply (string or structured response)

    Properties:
        id: Unique identifier from the runtime
        is_completed: Whether execution is complete
        status: Current execution status
        tool_calls: List of all tool calls from the runtime

    Usage:
        >>> from fivcplayground.agents.types import AgentMonitor, AgentRun
        >>> from fivcplayground import agents
        >>>
        >>> # Create monitor with optional event callback
        >>> def on_event(runtime: AgentRun):
        ...     # Access streaming text
        ...     print(f"Streaming: {runtime.streaming_text}", end="", flush=True)
        ...
        ...     # Access final reply
        ...     if runtime.reply:
        ...         print(f"Reply: {runtime.reply}")
        >>>
        >>> monitor = AgentMonitor(on_event=on_event)
        >>>
        >>> # Create agent with monitor as callback handler
        >>> agent = agents.create_companion_agent(callback_handler=monitor)
        >>>
        >>> # Execute and monitor automatically tracks execution
        >>> result = agent.run("What is 2+2?")
        >>>
        >>> # Access accumulated state via tool_calls property
        >>> tools = monitor.tool_calls
        >>>
        >>> # Reset for next execution with new callback
        >>> monitor.cleanup(on_event=on_event)

    Callback Events:
        The monitor receives events through __call__ method with different modes:
        - "start": Execution started, initializes runtime state
        - "messages": Streaming message chunks, accumulates streaming_text
        - "values": Final output values, stores reply (string or structured response)
        - "updates": State updates, clears streaming_text
        - "finish": Execution completed, marks status as COMPLETED
    """

    @property
    def id(self):
        return self._runtime.id

    @property
    def is_completed(self) -> bool:
        return self._runtime.is_completed

    @property
    def status(self) -> AgentRunStatus:
        return self._runtime.status

    def __init__(
        self,
        runtime: Optional[AgentRun] = None,
        runtime_repo: Optional[AgentRunRepository] = None,
        on_event: Optional[Callable[[AgentRun], None]] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize AgentMonitor.

        Args:
            runtime: Optional AgentRun instance to track execution state.
                     If not provided, a new AgentRun will be created.
            runtime_repo: Optional repository for persisting agent runtime state.
                         If not provided, a default FileAgentRunRepository will be created.
            on_event: Optional callback invoked after each event (streaming or tool).
                      Receives the complete AgentRun state, allowing access to
                      streaming_text, tool_calls, and other execution metadata.
            session_id: Optional session ID for grouping runtimes. If not provided,
                       will be created from agent_id or auto-generated.
        """
        from fivcplayground.agents.types.repositories.files import (
            FileAgentRunRepository,
        )

        self._runtime = runtime or AgentRun()
        self._repo = runtime_repo or FileAgentRunRepository()
        self._on_event = on_event
        self._session_id = session_id

        if not runtime:
            self._update_agent_runtime()

    def _update_agent_runtime(self):
        if self._session_id:
            self._repo.update_agent_run(self._session_id, self._runtime)

    def _fire_event(self):
        if self._on_event:
            self._on_event(self._runtime)

    def on_start(self, runtime: AgentRun):
        self._runtime = runtime
        self._update_agent_runtime()
        self._fire_event()

    def on_finish(self, runtime: AgentRun):
        if self._runtime is not runtime:
            import warnings

            warnings.warn(f"Agent mismatch: " f"{self._runtime.id} != {runtime.id}")

        self._update_agent_runtime()
        self._fire_event()

    def on_update(self, runtime: AgentRun):
        if self._runtime is not runtime:
            import warnings

            warnings.warn(f"Agent mismatch: " f"{self._runtime.id} != {runtime.id}")

        # self._update_agent_runtime()
        self._fire_event()

    def __call__(self, event: AgentRunEvent, runtime: AgentRun) -> None:
        try:
            if event == AgentRunEvent.START:
                self.on_start(runtime)

            elif event == AgentRunEvent.FINISH:
                self.on_finish(runtime)

            else:
                self.on_update(runtime)

        except Exception as e:
            # Gracefully handle callback exceptions
            import traceback

            print(f"Error in monitor callback: {e} {traceback.format_exc()}")

    @property
    def tool_calls(self) -> List[AgentRunToolCall]:
        """
        Get list of all tool calls from the runtime.

        Returns:
            List of AgentRunToolCall instances representing all tool
            invocations during the current execution.
        """
        return list(self._runtime.tool_calls.values())

    def cleanup(
        self,
        runtime: Optional[AgentRun] = None,
        on_event: Optional[Callable[[AgentRun], None]] = None,
    ) -> None:
        """
        Reset monitor state for a new execution.

        Replaces the current runtime with a new one (or the provided runtime)
        and optionally updates the event callback. This is typically called
        before starting a new agent execution to clear previous state.

        Args:
            runtime: Optional new AgentRun instance. If not provided,
                     a fresh AgentRun will be created.
            on_event: Optional new event callback. If not provided, the
                      callback will be cleared (set to None).
        """
        self._runtime = runtime or AgentRun()
        self._on_event = on_event


class AgentMonitorManager(object):
    """
    Centralized agent monitor manager for creating and monitoring agent executions.

    AgentMonitorManager provides a unified interface to:
    - Create agents with automatic monitoring integration
    - Track agent execution status through AgentMonitor
    - Persist agent execution history through AgentRunRepository
    - List and retrieve agent execution monitors
    - Delete agent execution records

    Note:
        The current implementation of create_agent_runtime() is incomplete.
        It only returns an empty AgentMonitor instance. The full implementation
        should accept query, agent_id, tool_retriever, and agent_creator parameters
        to create and monitor agent executions.

    Usage:
        >>> from fivcplayground.agents.types.monitors import AgentMonitorManager
        >>> from fivcplayground.agents.types.repositories.files import FileAgentRunRepository
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> # Create manager with file-based persistence
        >>> repo = FileAgentRunRepository(output_dir=OutputDir("./agents"))
        >>> manager = AgentMonitorManager(runtime_repo=repo)
        >>>
        >>> # View all agent executions for a specific agent
        >>> monitors = manager.list_agent_runtimes(agent_id)  # Returns list of AgentMonitor
        >>>
        >>> # Get specific agent execution monitor
        >>> agent_monitor = manager.get_agent_runtime(agent_id, agent_run_id)
        >>> print(f"Status: {agent_monitor.status}")
        >>> print(f"Tool calls: {len(agent_monitor.tool_calls)}")
        >>>
        >>> # Delete an agent execution
        >>> manager.delete_agent_runtime(agent_id, agent_run_id)

    Note:
        The runtime_repo parameter is required for all operations.
    """

    def __init__(
        self,
        runtime_repo: Optional["AgentRunRepository"] = None,
        **kwargs,
    ):
        """
        Initialize AgentMonitorManager.

        Args:
            runtime_repo: AgentRunRepository instance for persisting agent runtime state.
                         Required parameter for tracking and storing agent execution history.
            **kwargs: Additional keyword arguments (reserved for future use)

        Raises:
            AssertionError: If runtime_repo is None

        Example:
            >>> from fivcplayground.agents.types.repositories.files import FileAgentRunRepository
            >>> from fivcplayground.utils import OutputDir
            >>>
            >>> repo = FileAgentRunRepository(output_dir=OutputDir("./agents"))
            >>> manager = AgentMonitorManager(runtime_repo=repo)
        """
        assert runtime_repo is not None, "runtime_repo is required"

        self._repo = runtime_repo

    def create_agent_runtime(
        self,
        on_event: Optional[Callable[[AgentRun], None]] = None,
    ) -> AgentMonitor:
        """
        Create an agent runtime monitor.

        Creates a new AgentMonitor instance for tracking agent execution.

        Note:
            This implementation is incomplete. The full implementation should:
            - Accept query, agent_id, tool_retriever, and agent_creator parameters
            - Retrieve tools based on the query
            - Generate a unique agent ID if not provided
            - Load previous agent messages from the repository for conversation continuity
            - Create an AgentRun instance to track execution
            - Create an agent using the provided agent_creator
            - Return the created agent (not just the monitor)

        Args:
            on_event: Optional callback invoked with AgentRun after each agent event

        Returns:
            AgentMonitor: A monitor instance for tracking agent execution

        Example:
            >>> manager = AgentMonitorManager(runtime_repo=repo)
            >>> monitor = manager.create_agent_runtime(on_event=my_callback)
        """
        return AgentMonitor(
            on_event=on_event,
            runtime=AgentRun(),
            runtime_repo=self._repo,
        )

    def list_agent_runtimes(
        self, agent_id: str, status: Optional[List[AgentRunStatus]] = None
    ) -> List[AgentMonitor]:
        """
        Get list of all agent runtime monitors.

        Args:
            agent_id: Agent ID to list runtimes for
            status: Optional list of statuses to filter by

        Returns:
            List of AgentMonitor instances
        """
        # Get the session for this agent_id
        session = self._repo.get_agent_run_session(agent_id)
        if not session:
            return []

        agent_runtimes = self._repo.list_agent_runs(session.id)
        if status:
            return [
                AgentMonitor(
                    runtime=runtime, runtime_repo=self._repo, session_id=session.id
                )
                for runtime in agent_runtimes
                if runtime.status in status
            ]

        else:
            return [
                AgentMonitor(
                    runtime=runtime, runtime_repo=self._repo, session_id=session.id
                )
                for runtime in agent_runtimes
            ]

    def get_agent_runtime(
        self,
        agent_id: str,
        agent_run_id: str,
        on_event: Optional[Callable[[AgentRun], None]] = None,
    ) -> Optional[AgentMonitor]:
        """
        Get an agent runtime monitor by ID.

        Args:
            agent_id: Agent ID to retrieve
            agent_run_id: Agent run ID to retrieve
            on_event: Optional callback invoked with AgentRun after each agent event

        Returns:
            AgentMonitor instance or None if not found
        """
        # Get the session for this agent_id
        session = self._repo.get_agent_run_session(agent_id)
        if not session:
            return None

        agent_runtime = self._repo.get_agent_run(session.id, agent_run_id)
        if not agent_runtime:
            return None

        return AgentMonitor(
            runtime=agent_runtime,
            runtime_repo=self._repo,
            on_event=on_event,
            session_id=session.id,
        )

    def delete_agent_runtime(self, agent_id: str, agent_run_id: str) -> None:
        """
        Delete an agent runtime execution.

        Args:
            agent_id: Agent ID to delete
            agent_run_id: Agent run ID to delete
        """
        # Get the session for this agent_id
        session = self._repo.get_agent_run_session(agent_id)
        if session:
            self._repo.delete_agent_run(session.id, agent_run_id)
