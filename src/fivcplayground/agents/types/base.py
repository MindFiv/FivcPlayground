"""
Agent runtime data models.

This module defines the core data models for single-agent execution tracking
and metadata management. These models form the foundation of the agent runtime
system, providing structured data for agent configuration, execution state,
and tool invocations.

Core Models:
    - AgentRunSession: Agent configuration and metadata
    - AgentRun: Overall agent execution state and runtime data
    - AgentRunToolCall: Individual tool call record
    - AgentRunStatus: Execution status enumeration

These models use Pydantic for validation and serialization, making them
suitable for:
    - Persistence in repositories (file-based, database, etc.)
    - API communication and data exchange
    - Type-safe data validation
    - JSON serialization/deserialization

Example:
    >>> from fivcplayground.agents.types import (
    ...     AgentRunSession,
    ...     AgentRun,
    ...     AgentRunToolCall,
    ...     AgentRunStatus
    ... )
    >>>
    >>> # Create agent session metadata
    >>> session = AgentRunSession(
    ...     agent_id="my-agent",
    ...     description="A helpful assistant agent"
    ... )
    >>>
    >>> # Create runtime instance
    >>> runtime = AgentRun(
    ...     agent_id="my-agent",
    ...     status=AgentRunStatus.EXECUTING
    ... )

Note:
    For agent execution, see AgentRunnable in fivcadvisor.agents.types.backends
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4

from pydantic import (
    BaseModel,
    Field,
    computed_field,
)


class AgentConfig(BaseModel):
    """Agent configuration."""

    id: str = Field(..., description="Unique identifier for the agent")

    @computed_field
    @property
    def name(self) -> str:
        return self.id  # id and name are the same for agents

    model_id: str | None = Field(
        default=None, description="Model name (e.g., 'default', 'chat')"
    )
    description: str | None = Field(
        default=None, description="Description of the agent"
    )
    system_prompt: str | None = Field(
        default=None, description="System prompt/instructions for the agent"
    )


class AgentRunContent(BaseModel):
    text: str | None = Field(default=None, description="Text content")

    # TODO: add other content types as needed

    def __str__(self):
        return self.text


class AgentRunStatus(str, Enum):
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
        >>> runtime = AgentRun(
        ...     agent_id="my-agent",
        ...     status=AgentRunStatus.PENDING
        ... )
        >>> runtime.status = AgentRunStatus.EXECUTING
        >>> # ... agent processes ...
        >>> runtime.status = AgentRunStatus.COMPLETED

    Note:
        This enum inherits from str, making it JSON-serializable and
        compatible with string comparisons.
    """

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRunEvent(str, Enum):
    START = "start"
    FINISH = "finish"
    UPDATE = "update"
    STREAM = "stream"
    TOOL = "tool"  # tool call


class AgentRunToolCall(BaseModel):
    """
    Single tool call record.

    Represents a single tool invocation during agent execution, tracking
    the complete lifecycle of a tool call from invocation to completion.
    Each tool call captures the input parameters, execution result, timing
    information, and any errors that occurred.

    Attributes:
        id: Unique identifier for this tool call (required)
        tool_id: Identifier of the tool being invoked (required)
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
        >>> tool_call = AgentRunToolCall(
        ...     id="call-123",
        ...     tool_id="calculator",
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
        - id and tool_id are required fields
        - status should be one of: "pending", "success", "error"
        - duration is automatically calculated from timestamps
        - is_completed returns True for both "success" and "error" statuses
    """

    id: str = Field(description="Unique tool call identifier")
    tool_id: str = Field(description="Identifier of the tool being invoked")
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


class AgentRunSession(BaseModel):
    """
    Agent session metadata.

    Represents the metadata and configuration for an agent session, including
    agent identification and session tracking.

    Attributes:
        id: Unique session identifier
        agent_id: Unique agent identifier
        description: Description of agent's purpose and capabilities (optional)
        started_at: Timestamp when the agent session was created (optional)

    Example:
        >>> session = AgentRunSession(
        ...     agent_id="my-agent",
        ...     description="A helpful assistant agent"
        ... )
    """

    model_config = {"arbitrary_types_allowed": True}

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique session identifier (auto-generated if not provided)",
    )
    agent_id: str = Field(..., description="Unique agent identifier")
    description: str | None = Field(
        default=None, description="Description of agent's purpose and capabilities"
    )
    started_at: datetime | None = Field(
        default=None, description="Timestamp when the agent session was created"
    )


class AgentRun(BaseModel):
    """
    Agent execution state and runtime metadata.

    Represents the complete state of a single agent execution instance, tracking
    everything from initialization through completion. This includes execution
    status, timing information, tool calls, streaming output, and final results.

    Each AgentRun instance represents one execution of an agent, identified
    by a unique timestamp-based id. Multiple runtimes can exist for
    the same agent (identified by agent_id).

    Attributes:
        id: Unique run identifier (timestamp string, auto-generated)
        agent_id: ID of the agent being executed (optional)
        status: Current execution status (PENDING, EXECUTING, COMPLETED, FAILED)
        started_at: Timestamp when execution started
        completed_at: Timestamp when execution finished
        query: User query that initiated this agent run
        tool_calls: Dictionary mapping tool id to AgentRunToolCall instances
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
        >>> runtime = AgentRun(
        ...     agent_id="my-agent",
        ...     query="What is 2+2?",
        ...     status=AgentRunStatus.PENDING
        ... )
        >>>
        >>> # Start execution
        >>> runtime.status = AgentRunStatus.EXECUTING
        >>> runtime.started_at = datetime.now()
        >>>
        >>> # Add tool call
        >>> tool_call = AgentRunToolCall(
        ...     id="call-1",
        ...     tool_id="calculator",
        ...     tool_input={"expression": "2+2"}
        ... )
        >>> runtime.tool_calls[tool_call.id] = tool_call
        >>>
        >>> # Complete execution
        >>> runtime.status = AgentRunStatus.COMPLETED
        >>> runtime.completed_at = datetime.now()
        >>> print(f"Duration: {runtime.duration}s")
        >>> print(f"Tool calls: {runtime.tool_call_count}")

    Note:
        - id is auto-generated as a timestamp if not provided
        - tool_calls are stored separately in repositories (not in run.json)
        - Use AgentRunStatus enum for status values
        - Computed fields are automatically included in serialization
    """

    model_config = {"arbitrary_types_allowed": True}

    id: str = Field(
        default_factory=lambda: str(datetime.now().timestamp()),
        description="Unique run identifier (timestamp string for chronological ordering)",
    )
    agent_id: Optional[str] = Field(
        default=None, description="ID of the agent being executed"
    )
    status: AgentRunStatus = Field(
        default=AgentRunStatus.PENDING,
        description="Current execution status (PENDING, EXECUTING, COMPLETED, FAILED)",
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Timestamp when execution started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when execution finished"
    )
    query: Optional[AgentRunContent] = Field(
        default=None, description="User query that initiated this agent run"
    )
    tool_calls: Dict[str, AgentRunToolCall] = Field(
        default_factory=dict,
        description="Dictionary mapping tool id to AgentRunToolCall instances",
    )
    reply: Optional[AgentRunContent] = Field(
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
            >>> runtime.status = AgentRunStatus.EXECUTING
            >>> runtime.is_running
            True
        """
        return self.status == AgentRunStatus.EXECUTING

    @computed_field
    @property
    def is_completed(self) -> bool:
        """
        Check if execution has completed (successfully or with failure).

        Returns:
            True if status is COMPLETED or FAILED, False otherwise

        Example:
            >>> runtime.status = AgentRunStatus.COMPLETED
            >>> runtime.is_completed
            True
            >>> runtime.status = AgentRunStatus.FAILED
            >>> runtime.is_completed
            True
        """
        return self.status in (AgentRunStatus.COMPLETED, AgentRunStatus.FAILED)

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
