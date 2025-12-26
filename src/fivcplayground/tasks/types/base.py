__all__ = [
    "TaskAssessment",
    "TaskRequirement",
    "TaskTeam",
    "TaskRunContent",
    "TaskRunStatus",
    "TaskRunEvent",
    "TaskRunStage",
    "TaskRun",
    "TaskRunnable",
    "TaskSimpleRunnable",
]

import uuid
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field

from fivcplayground.agents import (
    AgentRunStatus as TaskRunStatus,
    AgentRunContent as TaskRunContent,
    AgentRunnable as TaskRunnable,
)


class TaskConfig(BaseModel):
    """Task configuration."""

    id: str = Field(..., description="Unique identifier for the task")


class TaskRunEvent(str, Enum):
    """Task runtime event enumeration."""

    START = "start"
    FINISH = "finish"
    UPDATE = "update"


class TaskAssessment(BaseModel):
    """Assessment result for task complexity."""

    model_config = {"populate_by_name": True}

    require_planning: bool = Field(
        description="Whether a planning agent is required to break down the task",
        alias="requires_planning_agent",
    )
    reasoning: str = Field(default="", description="Reasoning for the assessment")


class TaskRequirement(BaseModel):
    """Tool requirements for a task."""

    tools: List[str] = Field(description="List of tools needed for the task")


class TaskTeam(BaseModel):
    """Description for a plan for a task."""

    class Specialist(BaseModel):
        """Description for a planning task."""

        name: str = Field(description="Name of the agent for this task")
        backstory: str = Field(description="Backstory for the agent")
        tools: List[str] = Field(description="List of tools needed for the agent")

    specialists: List[Specialist] = Field(
        description="List of agents needed for the task"
    )


class TaskRunStage(BaseModel):
    """Single task execution step record."""

    model_config = {"arbitrary_types_allowed": True}

    id: str = Field(default=None, description="Unique identifier for the step")

    @computed_field
    @property
    def agent_id(self) -> str:  # same as id
        return self.id

    agent_name: str = Field(description="Name of the agent")

    status: TaskRunStatus = Field(
        default=TaskRunStatus.PENDING, description="Current execution status"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Step start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Step completion timestamp"
    )
    messages: List[TaskRunContent] = Field(
        default_factory=list, description="Messages during execution"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")

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
        """Check if execution is currently runtime"""
        return self.status == TaskRunStatus.EXECUTING

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)"""
        return self.status in (TaskRunStatus.COMPLETED, TaskRunStatus.FAILED)


class TaskRun(BaseModel):
    """Task runtime execution metadata."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique task ID"
    )

    @computed_field
    @property
    def task_id(self) -> str:  # same as id
        return self.id

    query: Optional[str] = Field(default=None, description="User query for the task")
    team: Optional[TaskTeam] = Field(
        default=None, description="Task team plan (if available)"
    )
    status: TaskRunStatus = Field(
        default=TaskRunStatus.PENDING, description="Current execution status"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Task start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Task completion timestamp"
    )
    steps: Dict[str, TaskRunStage] = Field(
        default_factory=dict, description="Task execution steps"
    )

    @computed_field
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if task is completed (success or failure)"""
        return self.status in (TaskRunStatus.COMPLETED, TaskRunStatus.FAILED)

    def sync_status(self):
        """Synchronize task status based on step statuses."""
        if any(step.status == TaskRunStatus.EXECUTING for step in self.steps.values()):
            self.status = TaskRunStatus.EXECUTING
        elif any(step.status == TaskRunStatus.FAILED for step in self.steps.values()):
            self.status = TaskRunStatus.FAILED
        elif all(
            step.status == TaskRunStatus.COMPLETED for step in self.steps.values()
        ):
            self.status = TaskRunStatus.COMPLETED
        else:
            self.status = TaskRunStatus.PENDING

    def sync_started_at(self):
        """Synchronize task start timestamp based on step timestamps."""
        if self.steps:
            self.started_at = min(
                step.started_at for step in self.steps.values() if step.started_at
            )

    def sync_completed_at(self):
        """Synchronize task completion timestamp based on step timestamps."""
        if self.steps:
            self.completed_at = max(
                step.completed_at for step in self.steps.values() if step.completed_at
            )

    def sync(self) -> "TaskRun":
        """Synchronize all task metadata based on step data."""
        self.sync_status()
        self.sync_started_at()
        self.sync_completed_at()
        return self

    def cleanup(self):
        """Clean up task data and reset to initial state."""
        self.status = TaskRunStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.steps.clear()


class TaskSimpleRunnable(TaskRunnable):
    """
    Simple task runnable for testing and development.

    This class provides a basic implementation of the Runnable interface
    for testing and development purposes. It does not perform any actual
    task execution, but simply returns a predefined result.
    """

    def __init__(self, runnable: TaskRunnable, query: str = "", **kwargs):
        self._query = query
        self._kwargs = kwargs
        self._runnable = runnable

    @property
    def id(self) -> str:
        return self._runnable.id

    @property
    def name(self) -> str:
        return self._runnable.name

    @property
    def description(self) -> str:
        return self._runnable.description

    def run(self, query: str = "", **kwargs) -> BaseModel:
        kwargs.update(query=self._query.format(query=query))
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return self._runnable.run(**kwargs)

    async def run_async(self, query: str = "", **kwargs) -> BaseModel:
        kwargs.update(query=self._query.format(query=query))
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return await self._runnable.run_async(**kwargs)
