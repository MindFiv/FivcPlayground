"""
Agent runtime data models.

This module defines the core data models for single-agent execution tracking
and metadata management. These models form the foundation of the agent runtime
system, providing structured data for agent configuration, execution state,
and tool invocations.

Core Models:
    - AgentsRuntimeMeta: Agent configuration and metadata
    - AgentsRuntime: Overall agent execution state and runtime data
    - AgentsRuntimeToolCall: Individual tool call record
    - AgentsStatus: Execution status enumeration

These models use Pydantic for validation and serialization, making them
suitable for:
    - Persistence in repositories (file-based, database, etc.)
    - API communication and data exchange
    - Type-safe data validation
    - JSON serialization/deserialization

Example:
    >>> from fivcplayground.agents.types import (
    ...     AgentsRuntimeMeta,
    ...     AgentsRuntime,
    ...     AgentsRuntimeToolCall,
    ...     AgentsStatus
    ... )
    >>>
    >>> # Create agent metadata
    >>> agent_meta = AgentsRuntimeMeta(
    ...     agent_id="my-agent",
    ...     agent_name="MyAgent",
    ...     system_prompt="You are a helpful assistant"
    ... )
    >>>
    >>> # Create runtime instance
    >>> runtime = AgentsRuntime(
    ...     agent_id="my-agent",
    ...     agent_name="MyAgent",
    ...     status=AgentsStatus.EXECUTING
    ... )

Note:
    For agent execution, see AgentsRunnable in fivcadvisor.agents.types.backends
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import (
    BaseModel,
    Field,
    computed_field,
)


class AgentsStatus(str, Enum):
    """
    Agent execution status enumeration.

    Defines the possible states of an agent runtime execution. The status
    progresses through a lifecycle from PENDING to either COMPLETED or FAILED.

    Attributes:
        PENDING: Agent runtime created but not yet started
        EXECUTING: Agent is currently running and processing
        COMPLETED: Agent finished successfully
        FAILED: Agent encountered an error and stopped

    Example:
        >>> runtime = AgentsRuntime(
        ...     agent_id="my-agent",
        ...     status=AgentsStatus.PENDING
        ... )
        >>> runtime.status = AgentsStatus.EXECUTING
        >>> # ... agent processes ...
        >>> runtime.status = AgentsStatus.COMPLETED

    Note:
        This enum inherits from str, making it JSON-serializable and
        compatible with string comparisons.
    """

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentsEvent(str, Enum):
    START = "start"
    FINISH = "finish"
    UPDATE = "update"
    STREAM = "stream"
    TOOL = "tool"  # tool call


class AgentsContent(BaseModel):
    text: Optional[str] = Field(description="Text content")
    # TODO: add other content types as needed


class AgentsRuntimeMeta(BaseModel):
    """
    Agent metadata and configuration.

    Stores the persistent configuration and identity information for an agent.
    This metadata is separate from runtime execution data and represents the
    agent's definition rather than a specific execution instance.

    Attributes:
        id: Computed field, same as agent_id for convenience
        agent_id: Unique identifier for the agent (required)
        agent_name: Human-readable name for the agent (optional)
        system_prompt: System prompt/instructions for the agent (optional)
        description: Description of the agent's purpose and capabilities (optional)

    Example:
        >>> agent_meta = AgentsRuntimeMeta(
        ...     agent_id="customer-support-agent",
        ...     agent_name="Customer Support Agent",
        ...     system_prompt="You are a helpful customer support assistant.",
        ...     description="Handles customer inquiries and support requests"
        ... )
        >>> print(agent_meta.id)  # Same as agent_id
        'customer-support-agent'

    Note:
        - Only agent_id is required; all other fields are optional
        - The id property is a computed field that mirrors agent_id
        - This model is typically stored in agent.json files in repositories
        - Use this for agent configuration, not runtime execution state
    """

    model_config = {"arbitrary_types_allowed": True}

    @computed_field
    @property
    def id(self) -> str:
        """
        Computed field providing convenient access to agent_id.

        Returns:
            The agent_id value
        """
        return self.agent_id

    agent_id: str = Field(description="Unique agent identifier")
    agent_name: Optional[str] = Field(
        default=None, description="Human-readable agent name"
    )
    system_prompt: Optional[str] = Field(
        default=None, description="System prompt/instructions for the agent"
    )
    description: Optional[str] = Field(
        default=None, description="Description of agent's purpose and capabilities"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the agent was first created"
    )


class AgentsRuntimeToolCall(BaseModel):
    """
    Single tool call record.

    Represents a single tool invocation during agent execution, tracking
    the complete lifecycle of a tool call from invocation to completion.
    Each tool call captures the input parameters, execution result, timing
    information, and any errors that occurred.

    Attributes:
        id: Computed field, same as tool_use_id for convenience
        tool_use_id: Unique identifier for this tool call (required)
        tool_name: Name of the tool being invoked (required)
        tool_input: Dictionary of input parameters passed to the tool
        tool_result: Result returned by the tool (None until completed)
        status: Current status - "pending", "success", or "error"
        started_at: Timestamp when the tool call started
        completed_at: Timestamp when the tool call finished
        error: Error message if the tool call failed
        duration: Computed field - execution time in seconds
        is_completed: Computed field - whether the call finished (success or error)

    Example:
        >>> # Create a pending tool call
        >>> tool_call = AgentsRuntimeToolCall(
        ...     tool_use_id="call-123",
        ...     tool_name="calculator",
        ...     tool_input={"expression": "2+2"},
        ...     status="pending",
        ...     started_at=datetime.now()
        ... )
        >>>
        >>> # Update with result
        >>> tool_call.status = "success"
        >>> tool_call.tool_result = 4
        >>> tool_call.completed_at = datetime.now()
        >>> print(f"Duration: {tool_call.duration}s")

    Note:
        - tool_use_id and tool_name are required fields
        - status should be one of: "pending", "success", "error"
        - duration is automatically calculated from timestamps
        - is_completed returns True for both "success" and "error" statuses
    """

    @computed_field
    @property
    def id(self) -> str:
        """
        Computed field providing convenient access to tool_use_id.

        Returns:
            The tool_use_id value
        """
        return self.tool_use_id

    tool_use_id: str = Field(description="Unique tool call identifier")
    tool_name: str = Field(description="Name of the tool being invoked")
    tool_input: Dict[str, Any] = Field(
        default_factory=dict, description="Input parameters passed to the tool"
    )
    tool_result: Optional[Any] = Field(
        default=None, description="Result returned by the tool (None until completed)"
    )
    status: str = Field(
        default="pending",
        description="Tool call status: 'pending', 'success', or 'error'",
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the tool call started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the tool call finished"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if the tool call failed"
    )

    @computed_field
    @property
    def duration(self) -> Optional[float]:
        """
        Get tool call execution duration in seconds.

        Calculates the time difference between started_at and completed_at.

        Returns:
            Duration in seconds if both timestamps are set, None otherwise

        Example:
            >>> tool_call.duration
            0.523  # 523 milliseconds
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @computed_field
    @property
    def is_completed(self) -> bool:
        """
        Check if tool call has completed (successfully or with error).

        Returns:
            True if status is "success" or "error", False if "pending"

        Example:
            >>> tool_call.status = "success"
            >>> tool_call.is_completed
            True
        """
        return self.status in ("success", "error")


class AgentsRuntime(BaseModel):
    """
    Agent execution state and runtime metadata.

    Represents the complete state of a single agent execution instance, tracking
    everything from initialization through completion. This includes execution
    status, timing information, tool calls, streaming output, and final results.

    Each AgentsRuntime instance represents one execution of an agent, identified
    by a unique timestamp-based agent_run_id. Multiple runtimes can exist for
    the same agent (identified by agent_id).

    Attributes:
        id: Computed field, same as agent_run_id for convenience
        agent_run_id: Unique run identifier (timestamp string, auto-generated)
        agent_id: ID of the agent being executed (optional)
        agent_name: Name of the agent (optional)
        status: Current execution status (PENDING, EXECUTING, COMPLETED, FAILED)
        started_at: Timestamp when execution started
        completed_at: Timestamp when execution finished
        query: User query that initiated this agent run
        tool_calls: Dictionary mapping tool_use_id to AgentsRuntimeToolCall instances
        reply: Final agent reply message
        streaming_text: Accumulated streaming text output from the agent
        error: Error message if execution failed
        duration: Computed field - execution time in seconds
        is_running: Computed field - whether agent is currently executing
        is_completed: Computed field - whether execution finished (success or failure)
        tool_call_count: Computed field - total number of tool calls
        successful_tool_calls: Computed field - count of successful tool calls
        failed_tool_calls: Computed field - count of failed tool calls

    Example:
        >>> # Create a new runtime
        >>> runtime = AgentsRuntime(
        ...     agent_id="my-agent",
        ...     agent_name="MyAgent",
        ...     query="What is 2+2?",
        ...     status=AgentsStatus.PENDING
        ... )
        >>>
        >>> # Start execution
        >>> runtime.status = AgentsStatus.EXECUTING
        >>> runtime.started_at = datetime.now()
        >>>
        >>> # Add tool call
        >>> tool_call = AgentsRuntimeToolCall(
        ...     tool_use_id="call-1",
        ...     tool_name="calculator",
        ...     tool_input={"expression": "2+2"}
        ... )
        >>> runtime.tool_calls[tool_call.tool_use_id] = tool_call
        >>>
        >>> # Complete execution
        >>> runtime.status = AgentsStatus.COMPLETED
        >>> runtime.completed_at = datetime.now()
        >>> print(f"Duration: {runtime.duration}s")
        >>> print(f"Tool calls: {runtime.tool_call_count}")

    Note:
        - agent_run_id is auto-generated as a timestamp if not provided
        - tool_calls are stored separately in repositories (not in run.json)
        - The id property is a computed field that mirrors agent_run_id
        - Use AgentsStatus enum for status values
        - Computed fields are automatically included in serialization
    """

    model_config = {"arbitrary_types_allowed": True}

    @computed_field
    @property
    def id(self) -> str:
        """
        Computed field providing convenient access to agent_run_id.

        Returns:
            The agent_run_id value
        """
        return self.agent_run_id

    agent_run_id: str = Field(
        default_factory=lambda: str(datetime.now().timestamp()),
        description="Unique run identifier (timestamp string for chronological ordering)",
    )
    agent_id: Optional[str] = Field(
        default=None, description="ID of the agent being executed"
    )
    agent_name: Optional[str] = Field(default=None, description="Name of the agent")
    status: AgentsStatus = Field(
        default=AgentsStatus.PENDING,
        description="Current execution status (PENDING, EXECUTING, COMPLETED, FAILED)",
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Timestamp when execution started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when execution finished"
    )
    query: Optional[AgentsContent] = Field(
        default=None, description="User query that initiated this agent run"
    )
    tool_calls: Dict[str, AgentsRuntimeToolCall] = Field(
        default_factory=dict,
        description="Dictionary mapping tool_use_id to AgentsRuntimeToolCall instances",
    )
    reply: Optional[AgentsContent] = Field(
        default=None, description="Final agent reply message"
    )
    streaming_text: str = Field(
        default="", description="Accumulated streaming text output from the agent"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )

    @computed_field
    @property
    def duration(self) -> Optional[float]:
        """
        Get total execution duration in seconds.

        Calculates the time difference between started_at and completed_at.

        Returns:
            Duration in seconds if both timestamps are set, None otherwise

        Example:
            >>> runtime.started_at = datetime(2024, 1, 1, 12, 0, 0)
            >>> runtime.completed_at = datetime(2024, 1, 1, 12, 0, 5)
            >>> runtime.duration
            5.0
        """
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @computed_field
    @property
    def is_running(self) -> bool:
        """
        Check if execution is currently running.

        Returns:
            True if status is EXECUTING, False otherwise

        Example:
            >>> runtime.status = AgentsStatus.EXECUTING
            >>> runtime.is_running
            True
        """
        return self.status == AgentsStatus.EXECUTING

    @computed_field
    @property
    def is_completed(self) -> bool:
        """
        Check if execution has completed (successfully or with failure).

        Returns:
            True if status is COMPLETED or FAILED, False otherwise

        Example:
            >>> runtime.status = AgentsStatus.COMPLETED
            >>> runtime.is_completed
            True
            >>> runtime.status = AgentsStatus.FAILED
            >>> runtime.is_completed
            True
        """
        return self.status in (AgentsStatus.COMPLETED, AgentsStatus.FAILED)

    @computed_field
    @property
    def tool_call_count(self) -> int:
        """
        Get total number of tool calls made during execution.

        Returns:
            Count of all tool calls in the tool_calls dictionary

        Example:
            >>> runtime.tool_calls = {
            ...     "call-1": tool_call_1,
            ...     "call-2": tool_call_2
            ... }
            >>> runtime.tool_call_count
            2
        """
        return len(self.tool_calls)

    @computed_field
    @property
    def successful_tool_calls(self) -> int:
        """
        Get number of successful tool calls.

        Counts tool calls with status "success".

        Returns:
            Count of successful tool calls

        Example:
            >>> # Assuming 2 successful and 1 failed tool call
            >>> runtime.successful_tool_calls
            2
        """
        return sum(1 for tc in self.tool_calls.values() if tc.status == "success")

    @computed_field
    @property
    def failed_tool_calls(self) -> int:
        """
        Get number of failed tool calls.

        Counts tool calls with status "error".

        Returns:
            Count of failed tool calls

        Example:
            >>> # Assuming 2 successful and 1 failed tool call
            >>> runtime.failed_tool_calls
            1
        """
        return sum(1 for tc in self.tool_calls.values() if tc.status == "error")
