from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type
from uuid import uuid4

from jambo import SchemaConverter
from pydantic import (
    BaseModel,
    Field,
    computed_field,
)

from fivcplayground.models import ModelBackend, ModelConfigRepository
from fivcplayground.skills import SkillRetriever
from fivcplayground.tools import ToolRetriever


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
    tool_ids: List[str] | None = Field(
        default=None, description="List of tool IDs to use with the agent"
    )
    description: str | None = Field(
        default=None, description="Description of the agent"
    )
    system_prompt: str | None = Field(
        default=None, description="System prompt/instructions for the agent"
    )
    response_format: Dict[str, Any] | None = Field(
        default=None, description="Response format for the agent in JSON Schema format"
    )

    @property
    def response_model(self) -> Type[BaseModel] | None:
        if not self.response_format:
            return None

        schema = self.response_format
        if "title" not in schema:
            schema = {**schema, "title": f"{self.id}_response"}

        try:
            return SchemaConverter.build(schema)
        except ValueError:
            print(f"Failed to build response model for agent {self.id}: {schema}")
            return None


class AgentRunContent(BaseModel):
    text: str | None = Field(default=None, description="Text content")
    structured: dict[str, Any] | None = Field(
        default=None, description="Structured content"
    )
    images: list[str] | None = Field(default=None, description="Image contents")
    files: list[str] | None = Field(default=None, description="File contents")

    def __str__(self):
        return self.text


class AgentRunStatus(str, Enum):
    """Agent execution status enumeration."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRunEvent(str, Enum):
    """Agent runtime event enumeration."""

    START = "start"
    FINISH = "finish"
    UPDATE = "update"
    STREAM = "stream"
    TOOL = "tool"  # tool call


class AgentRunToolSet(BaseModel):
    """Agent toolbox."""

    tool_ids: List[str] = Field(description="List of tool IDs to use with the agent")


class AgentRunToolCall(BaseModel):
    """Single tool call record."""

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
        """Get tool call duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if tool call is completed (success or failure)"""
        return self.status in ("success", "error")


class AgentRunSession(BaseModel):
    """Agent metadata and session information."""

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
    """Agent runtime execution metadata."""

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
    delta: Optional[AgentRunContent] = Field(
        default=None,
        exclude=True,
        description="Delta message from the agent streaming output. "
        "Contains only the new content chunk received in the current stream event, "
        "not the accumulated message. Can contain text, images, or files.",
    )
    error: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )

    @computed_field
    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @computed_field
    @property
    def is_running(self) -> bool:
        """Check if execution is currently running"""
        return self.status == AgentRunStatus.EXECUTING

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)"""
        return self.status in (AgentRunStatus.COMPLETED, AgentRunStatus.FAILED)

    @computed_field
    @property
    def tool_call_count(self) -> int:
        """Get total number of tool calls made during execution"""
        return len(self.tool_calls)

    @computed_field
    @property
    def successful_tool_calls(self) -> int:
        """Get number of successful tool calls"""
        return sum(1 for tc in self.tool_calls.values() if tc.status == "success")

    @computed_field
    @property
    def failed_tool_calls(self) -> int:
        """Get number of failed tool calls"""
        return sum(1 for tc in self.tool_calls.values() if tc.status == "error")


class AgentRunnable(ABC):
    """Abstract base class for agent runnable."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the agent runnable"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the agent runnable"""

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of the agent runnable"""

    @abstractmethod
    async def run_async(
        self,
        query: str | AgentRunContent = "",
        # agent_run_repository: 'AgentRunRepository' | None = None,
        # agent_run_session_id: str | None = None,
        tool_retriever: ToolRetriever | None = None,
        tool_ids: List[str] | None = None,
        skill_retriever: SkillRetriever | None = None,
        response_model: Type[BaseModel] | None = None,
        event_callback: Callable[[AgentRunEvent, AgentRun], None] = lambda e, r: None,
        **kwargs,  # ignore additional kwargs
    ) -> BaseModel:
        """Asynchronous execution of agent"""


class AgentBackend(ABC):
    """Interface for agent backends."""

    @abstractmethod
    async def create_agent_async(
        self,
        model_backend: ModelBackend,
        model_config_repository: ModelConfigRepository,
        agent_config: AgentConfig,
    ) -> AgentRunnable:
        """Create an agent instance from an AgentConfig."""
