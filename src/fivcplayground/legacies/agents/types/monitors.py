"""
Agent execution monitor for tracking single-agent execution.

This module provides monitoring and management classes for agent execution:

Core Classes:
    - AgentsMonitor: Tracks single agent execution through callback events
    - AgentsMonitorManager: Manages multiple agent executions with persistence

Features:
    - Real-time streaming text accumulation
    - Tool call event capture with status tracking
    - Unified callback pattern for execution events
    - Framework-agnostic design (no UI dependencies)
    - Graceful error handling for callbacks
    - Automatic persistence via AgentsRuntimeRepository
    - Conversation history management
    - Multi-turn agent support

Callback Pattern:
    The monitor uses a unified callback pattern where a single on_event callback
    receives the complete AgentsRuntime state after each event, allowing UI
    components to access all execution data in one place.

Integration with AgentsRunnable:
    AgentsMonitor integrates with AgentsRunnable through callback_handler parameter,
    capturing execution events and maintaining runtime state. The monitor receives
    string responses from AgentsRunnable and stores them in the runtime.

Key Features:
    - Unified callback-based execution tracking via AgentsRuntime
    - Real-time streaming message accumulation
    - Tool call event capture with status tracking
    - Framework-agnostic design (no UI dependencies)
    - Graceful error handling for callbacks
    - Cleanup method for resetting state between executions
    - Centralized agent lifecycle management through AgentsMonitorManager
    - Automatic agent creation with monitoring integration
"""

from typing import Optional, List, Callable

from fivcplayground.agents.types.base import (
    AgentsStatus,
    AgentsEvent,
    AgentsRuntime,
    AgentsRuntimeToolCall,
)
from fivcplayground.agents.types.repositories import (
    AgentsRuntimeRepository,
)


class AgentsMonitor(object):
    """
    Agent execution monitor for tracking single-agent execution.

    Tracks agent execution through callback events, capturing streaming text
    chunks and execution state in an AgentsRuntime object. Provides real-time
    callbacks for UI updates while maintaining framework-agnostic design.

    Integration with Runnable:
    The monitor is passed as callback_handler to Runnable and receives
    execution events through the __call__ method with different modes:
    - "start": Execution started
    - "messages": Streaming message chunks
    - "values": Final output values (including structured_response or messages)
    - "updates": State updates
    - "finish": Execution completed

    All events are accumulated in an AgentsRuntime object that tracks:
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
        >>> from fivcplayground.agents.types import AgentsMonitor, AgentsRuntime
        >>> from fivcplayground import agents
        >>>
        >>> # Create monitor with optional event callback
        >>> def on_event(runtime: AgentsRuntime):
        ...     # Access streaming text
        ...     print(f"Streaming: {runtime.streaming_text}", end="", flush=True)
        ...
        ...     # Access final reply
        ...     if runtime.reply:
        ...         print(f"Reply: {runtime.reply}")
        >>>
        >>> monitor = AgentsMonitor(on_event=on_event)
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
    def status(self) -> AgentsStatus:
        return self._runtime.status

    def __init__(
        self,
        runtime: Optional[AgentsRuntime] = None,
        runtime_repo: Optional[AgentsRuntimeRepository] = None,
        on_event: Optional[Callable[[AgentsRuntime], None]] = None,
    ):
        """
        Initialize AgentsMonitor.

        Args:
            runtime: Optional AgentsRuntime instance to track execution state.
                     If not provided, a new AgentsRuntime will be created.
            runtime_repo: Optional repository for persisting agent runtime state.
                         If not provided, a default FileAgentsRuntimeRepository will be created.
            on_event: Optional callback invoked after each event (streaming or tool).
                      Receives the complete AgentsRuntime state, allowing access to
                      streaming_text, tool_calls, and other execution metadata.
        """
        from fivcplayground.agents.types.repositories.files import (
            FileAgentsRuntimeRepository,
        )

        self._runtime = runtime or AgentsRuntime()
        self._repo = runtime_repo or FileAgentsRuntimeRepository()
        self._on_event = on_event

        if not runtime:
            self._update_agent_runtime()

    def _update_agent_runtime(self):
        if self._runtime.agent_id:
            self._repo.update_agent_runtime(self._runtime.agent_id, self._runtime)

    def _update_agent_runtime_tool_call(self, tool_call: AgentsRuntimeToolCall):
        if self._runtime.agent_id:
            self._repo.update_agent_runtime_tool_call(
                self._runtime.agent_id, self._runtime.agent_run_id, tool_call
            )

    def _fire_event(self):
        if self._on_event:
            self._on_event(self._runtime)

    def on_start(self, runtime: AgentsRuntime):
        self._runtime = runtime
        self._update_agent_runtime()
        self._fire_event()

    def on_finish(self, runtime: AgentsRuntime):
        if self._runtime is not runtime:
            import warnings

            warnings.warn(
                f"Agent mismatch: "
                f"{self._runtime.agent_run_id} != {runtime.agent_run_id}"
            )

        self._update_agent_runtime()
        for tool_call in self._runtime.tool_calls.values():
            self._update_agent_runtime_tool_call(tool_call)
        self._fire_event()

    def on_update(self, runtime: AgentsRuntime):
        if self._runtime is not runtime:
            import warnings

            warnings.warn(
                f"Agent mismatch: "
                f"{self._runtime.agent_run_id} != {runtime.agent_run_id}"
            )

        # self._update_agent_runtime()
        self._fire_event()

    def __call__(self, event: AgentsEvent, runtime: AgentsRuntime) -> None:
        try:
            if event == AgentsEvent.START:
                self.on_start(runtime)

            elif event == AgentsEvent.FINISH:
                self.on_finish(runtime)

            else:
                self.on_update(runtime)

        except Exception as e:
            # Gracefully handle callback exceptions
            import traceback

            print(f"Error in monitor callback: {e} {traceback.format_exc()}")

    @property
    def tool_calls(self) -> List[AgentsRuntimeToolCall]:
        """
        Get list of all tool calls from the runtime.

        Returns:
            List of AgentsRuntimeToolCall instances representing all tool
            invocations during the current execution.
        """
        return list(self._runtime.tool_calls.values())

    def cleanup(
        self,
        runtime: Optional[AgentsRuntime] = None,
        on_event: Optional[Callable[[AgentsRuntime], None]] = None,
    ) -> None:
        """
        Reset monitor state for a new execution.

        Replaces the current runtime with a new one (or the provided runtime)
        and optionally updates the event callback. This is typically called
        before starting a new agent execution to clear previous state.

        Args:
            runtime: Optional new AgentsRuntime instance. If not provided,
                     a fresh AgentsRuntime will be created.
            on_event: Optional new event callback. If not provided, the
                      callback will be cleared (set to None).
        """
        self._runtime = runtime or AgentsRuntime()
        self._on_event = on_event


class AgentsMonitorManager(object):
    """
    Centralized agent monitor manager for creating and monitoring agent executions.

    AgentsMonitorManager provides a unified interface to:
    - Create agents with automatic monitoring integration
    - Track agent execution status through AgentsMonitor
    - Persist agent execution history through AgentsRuntimeRepository
    - List and retrieve agent execution monitors
    - Delete agent execution records

    Note:
        The current implementation of create_agent_runtime() is incomplete.
        It only returns an empty AgentsMonitor instance. The full implementation
        should accept query, agent_id, tools_retriever, and agent_creator parameters
        to create and monitor agent executions.

    Usage:
        >>> from fivcplayground.agents.types.monitors import AgentsMonitorManager
        >>> from fivcplayground.agents.types.repositories.files import FileAgentsRuntimeRepository
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> # Create manager with file-based persistence
        >>> repo = FileAgentsRuntimeRepository(output_dir=OutputDir("./agents"))
        >>> manager = AgentsMonitorManager(runtime_repo=repo)
        >>>
        >>> # View all agent executions for a specific agent
        >>> monitors = manager.list_agent_runtimes(agent_id)  # Returns list of AgentsMonitor
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
        runtime_repo: Optional["AgentsRuntimeRepository"] = None,
        **kwargs,
    ):
        """
        Initialize AgentsMonitorManager.

        Args:
            runtime_repo: AgentsRuntimeRepository instance for persisting agent runtime state.
                         Required parameter for tracking and storing agent execution history.
            **kwargs: Additional keyword arguments (reserved for future use)

        Raises:
            AssertionError: If runtime_repo is None

        Example:
            >>> from fivcplayground.agents.types.repositories.files import FileAgentsRuntimeRepository
            >>> from fivcplayground.utils import OutputDir
            >>>
            >>> repo = FileAgentsRuntimeRepository(output_dir=OutputDir("./agents"))
            >>> manager = AgentsMonitorManager(runtime_repo=repo)
        """
        assert runtime_repo is not None, "runtime_repo is required"

        self._repo = runtime_repo

    def create_agent_runtime(
        self,
        on_event: Optional[Callable[[AgentsRuntime], None]] = None,
    ) -> AgentsMonitor:
        """
        Create an agent runtime monitor.

        Creates a new AgentsMonitor instance for tracking agent execution.

        Note:
            This implementation is incomplete. The full implementation should:
            - Accept query, agent_id, tools_retriever, and agent_creator parameters
            - Retrieve tools based on the query
            - Generate a unique agent ID if not provided
            - Load previous agent messages from the repository for conversation continuity
            - Create an AgentsRuntime instance to track execution
            - Create an agent using the provided agent_creator
            - Return the created agent (not just the monitor)

        Args:
            on_event: Optional callback invoked with AgentsRuntime after each agent event

        Returns:
            AgentsMonitor: A monitor instance for tracking agent execution

        Example:
            >>> manager = AgentsMonitorManager(runtime_repo=repo)
            >>> monitor = manager.create_agent_runtime(on_event=my_callback)
        """
        return AgentsMonitor(
            on_event=on_event,
            runtime=AgentsRuntime(),
            runtime_repo=self._repo,
        )

    def list_agent_runtimes(
        self, agent_id: str, status: Optional[List[AgentsStatus]] = None
    ) -> List[AgentsMonitor]:
        """
        Get list of all agent runtime monitors.

        Args:
            agent_id: Agent ID to list runtimes for
            status: Optional list of statuses to filter by

        Returns:
            List of AgentsMonitor instances
        """
        agent_runtimes = self._repo.list_agent_runtimes(agent_id)
        if status:
            return [
                AgentsMonitor(runtime=runtime, runtime_repo=self._repo)
                for runtime in agent_runtimes
                if runtime.status in status
            ]

        else:
            return [
                AgentsMonitor(runtime=runtime, runtime_repo=self._repo)
                for runtime in agent_runtimes
            ]

    def get_agent_runtime(
        self,
        agent_id: str,
        agent_run_id: str,
        on_event: Optional[Callable[[AgentsRuntime], None]] = None,
    ) -> Optional[AgentsMonitor]:
        """
        Get an agent runtime monitor by ID.

        Args:
            agent_id: Agent ID to retrieve
            agent_run_id: Agent run ID to retrieve
            on_event: Optional callback invoked with AgentsRuntime after each agent event

        Returns:
            AgentsMonitor instance or None if not found
        """
        agent_runtime = self._repo.get_agent_runtime(agent_id, agent_run_id)
        if not agent_runtime:
            return None

        return AgentsMonitor(
            runtime=agent_runtime,
            runtime_repo=self._repo,
            on_event=on_event,
        )

    def delete_agent_runtime(self, agent_id: str, agent_run_id: str) -> None:
        """
        Delete an agent runtime execution.

        Args:
            agent_id: Agent ID to delete
            agent_run_id: Agent run ID to delete
        """
        self._repo.delete_agent_runtime(agent_id, agent_run_id)
