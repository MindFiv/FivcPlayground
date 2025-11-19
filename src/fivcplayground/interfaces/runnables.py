from abc import abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, List
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field
from fivcglue import IComponent


class RunnableStatus(str, Enum):
    """
    Execution status of a runnable.
    """

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class RunnableContent(BaseModel):
    """
    Content for a runnable execution.
    """

    text: str | None = None

    def __str__(self):
        return self.text or ""


class RunnableTraceToolCall(BaseModel):
    """
    Trace of a tool call within a runnable execution.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique tool call ID"
    )
    name: str = Field(description="Name of the tool")
    input: dict | None = Field(
        default=None, description="Input parameters passed to the tool"
    )
    output: dict | list | str | int | float | None = Field(
        default=None, description="Output result from the tool"
    )
    status: RunnableStatus = Field(
        default=RunnableStatus.PENDING, description="Current execution status"
    )
    started_at: datetime | None = Field(
        default=None, description="Timestamp when the tool call started"
    )
    completed_at: datetime | None = Field(
        default=None, description="Timestamp when the tool call finished"
    )

    @computed_field
    @property
    def duration(self) -> float | None:
        return (
            (self.completed_at - self.started_at).total_seconds()
            if (self.started_at and self.completed_at)
            else None
        )

    @computed_field
    @property
    def is_running(self) -> bool:
        return self.started_at is not None and self.completed_at is None

    @computed_field
    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None


class RunnableTrace(BaseModel):
    """
    Trace of a runnable execution.
    """

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique log entry ID"
    )
    status: RunnableStatus = Field(
        default=RunnableStatus.PENDING, description="Current execution status"
    )
    started_at: datetime | None = Field(
        default=None, description="Timestamp when execution started"
    )
    completed_at: datetime | None = Field(
        default=None, description="Timestamp when execution finished"
    )
    query: RunnableContent | None = Field(
        default=None, description="Input query to the runnable"
    )
    reply: RunnableContent | None = Field(
        default=None, description="Output reply from the runnable"
    )
    delta: RunnableContent | None = Field(
        default=None, description="Streaming delta content"
    )
    tool_calls: dict[str, RunnableTraceToolCall] = Field(
        default_factory=dict, description="Dictionary mapping tool ID to tool trace"
    )

    @computed_field
    @property
    def duration(self) -> float | None:
        return (
            (self.completed_at - self.started_at).total_seconds()
            if (self.started_at and self.completed_at)
            else None
        )

    @computed_field
    @property
    def is_running(self) -> bool:
        return self.started_at is not None and self.completed_at is None

    @computed_field
    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None


class IRunnableCallback(IComponent):
    """
    Interface for runnable callbacks.
    """

    @abstractmethod
    def on_start(self, trace: RunnableTrace) -> None:
        """
        Callback for when execution starts.
        """

    @abstractmethod
    def on_finish(self, trace: RunnableTrace) -> None:
        """
        Callback for when execution finishes.
        """

    @abstractmethod
    def on_update(self, trace: RunnableTrace) -> None:
        """
        Callback for when execution updates.
        """

    @abstractmethod
    def on_tool(self, trace: RunnableTrace) -> None:
        """
        Callback for when a tool is used.
        """

    @abstractmethod
    def on_delta(self, trace: RunnableTrace) -> None:
        """
        Callback for when streaming delta is received.
        """


class IRunnableSession(IComponent):
    """
    Interface for runnable session.
    """

    def set_trace(self, trace: RunnableTrace) -> None:
        """Update the trace."""
        ...

    def get_trace(self, trace_id: str) -> RunnableTrace | None:
        """Get the trace."""
        ...

    def list_traces(self, **kwargs: Any) -> List[RunnableTrace]:
        """List the traces."""
        ...


class IRunnable(IComponent):
    """
    Interface for runnable objects that support sync and async execution.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Unique identifier for the runnable.
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the runnable.
        """

    @abstractmethod
    async def run_async(
        self, query: str | RunnableContent = "", **kwargs: Any
    ) -> RunnableTrace:
        """
        Execute the runnable asynchronously (abstract method).
        """

    @abstractmethod
    def run(
        self,
        query: str | RunnableContent = "",
        **kwargs: Any,
    ) -> RunnableTrace:
        """
        Execute the runnable synchronously (abstract method).
        """

    def __call__(self, **kwargs: Any) -> Any:
        return self.run(**kwargs)


class RunnableProxy(IRunnable):
    """
    Proxy runnable that delegates to another runnable.

    This class provides a proxy implementation of the Runnable interface that
    forwards all execution to a wrapped runnable. It can be used to add
    additional behavior or preprocessing before delegating to the underlying
    runnable.
    """

    def __init__(self, runnable: IRunnable, **kwargs: Any):
        self._runnable = runnable
        self._kwargs = kwargs

    @property
    def id(self) -> str:
        return self._runnable.id

    @property
    def name(self) -> str:
        return self._runnable.name

    async def run_async(self, **kwargs: Any) -> Any:
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return await self._runnable.run_async(**kwargs)

    def run(self, **kwargs: Any) -> Any:
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return self._runnable.run(**kwargs)
