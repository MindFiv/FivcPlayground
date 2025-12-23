"""
Task runtime data models.

This module defines the core data models for task execution tracking:
    - TaskAssessment: Assessment result for task complexity
    - TaskRequirement: Tool requirements for a task
    - TaskTeam: Team plan with specialist agents
    - TaskRuntimeStep: Individual agent execution step
    - TaskRuntime: Overall task execution state
    - TaskStatus: Execution status enumeration

These models use Pydantic for validation and serialization, making them
suitable for persistence and API communication.
"""

import uuid
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field

from fivcplayground.agents import AgentRunContent, AgentRunnable


class TaskStatus(str, Enum):
    """Task execution status enumeration."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskEvent(str, Enum):
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


class TaskRuntimeStep(BaseModel):
    """Single task execution step record."""

    model_config = {"arbitrary_types_allowed": True}

    id: str = Field(default=None, description="Unique identifier for the step")

    @computed_field
    @property
    def agent_id(self) -> str:  # same as id
        return self.id

    agent_name: str = Field(description="Name of the agent")

    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current execution status"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Step start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Step completion timestamp"
    )
    messages: List[AgentRunContent] = Field(
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
        return self.status == TaskStatus.EXECUTING

    @computed_field
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)"""
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)


class TaskRuntime(BaseModel):
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
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current execution status"
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Task start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Task completion timestamp"
    )
    steps: Dict[str, TaskRuntimeStep] = Field(
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
        return self.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)

    def sync_status(self):
        """
        Synchronize task status based on step statuses.

        Updates the task status according to the following rules:
        - EXECUTING: If any step is currently executing
        - FAILED: If any step has failed
        - COMPLETED: If all steps are completed
        - PENDING: Otherwise (no steps or all pending)
        """
        if any(step.status == TaskStatus.EXECUTING for step in self.steps.values()):
            self.status = TaskStatus.EXECUTING
        elif any(step.status == TaskStatus.FAILED for step in self.steps.values()):
            self.status = TaskStatus.FAILED
        elif all(step.status == TaskStatus.COMPLETED for step in self.steps.values()):
            self.status = TaskStatus.COMPLETED
        else:
            self.status = TaskStatus.PENDING

    def sync_started_at(self):
        """
        Synchronize task start timestamp based on step timestamps.

        Sets started_at to the earliest step start time.
        Does nothing if no steps have started.
        """
        if self.steps:
            self.started_at = min(
                step.started_at for step in self.steps.values() if step.started_at
            )

    def sync_completed_at(self):
        """
        Synchronize task completion timestamp based on step timestamps.

        Sets completed_at to the latest step completion time.
        Does nothing if no steps have completed.
        """
        if self.steps:
            self.completed_at = max(
                step.completed_at for step in self.steps.values() if step.completed_at
            )

    def sync(self) -> "TaskRuntime":
        """
        Synchronize all task metadata based on step data.

        Calls sync_status(), sync_started_at(), and sync_completed_at()
        to update task-level metadata from step-level data.

        Returns:
            Self for method chaining
        """
        self.sync_status()
        self.sync_started_at()
        self.sync_completed_at()
        return self

    def cleanup(self):
        """
        Clean up task data and reset to initial state.

        Resets status to PENDING, clears timestamps, and removes all steps.
        Use this to prepare a task for reuse or before deletion.
        """
        self.status = TaskStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.steps.clear()


class TaskSimpleRunnable(AgentRunnable):
    """
    Simple task runnable for testing and development.

    This class provides a basic implementation of the Runnable interface
    for testing and development purposes. It does not perform any actual
    task execution, but simply returns a predefined result.
    """

    def __init__(self, runnable: AgentRunnable, query: str = "", **kwargs):
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
