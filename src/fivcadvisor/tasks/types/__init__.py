"""
Task types module.

Provides types, models, and utilities for task execution tracking, persistence,
and execution management.

Task Models (Pydantic):
    - TaskAssessment: Assessment result for task complexity and planning needs
    - TaskRequirement: Tool requirements for a task
    - TaskTeam: Team plan with specialist agents for complex tasks
    - TaskStatus: Execution status enumeration (PENDING, EXECUTING, COMPLETED, FAILED)
    - TaskRuntimeStep: Individual agent execution step with timing and messages
    - TaskRuntime: Overall task execution state and metadata

Task Execution and Monitoring:
    - TaskRunnable: Wrapper for task-specific agent execution
    - TaskMonitor: Tracks agent execution through hook events
    - TaskMonitorManager: Manages multiple tasks with centralized monitoring

Task Persistence:
    - TaskRuntimeRepository: Abstract interface for task persistence

Usage Example:
    >>> from fivcadvisor.tasks.types import TaskMonitor, TaskStatus
    >>> from fivcadvisor.tasks.types.repositories.files import FileTaskRuntimeRepository
    >>>
    >>> # Create a monitor with file persistence
    >>> repo = FileTaskRuntimeRepository(output_dir="./tasks")
    >>> monitor = TaskMonitor(runtime_repo=repo)
    >>>
    >>> # Use with agent execution
    >>> swarm = create_agent_swarm(hooks=[monitor])
    >>> result = swarm.run("Execute task")
    >>>
    >>> # Query task status
    >>> runtime = monitor.get_runtime()
    >>> print(f"Status: {runtime.status}")
    >>> print(f"Steps: {len(runtime.steps)}")
"""

__all__ = [
    "TaskAssessment",
    "TaskRequirement",
    "TaskTeam",
    "TaskMonitor",
    "TaskEvent",
    "TaskRuntimeStep",
    "TaskRuntime",
    "TaskRuntimeRepository",
    "TaskStatus",
    "TaskMonitorManager",
    "TaskRunnable",
]

from .base import (
    TaskAssessment,
    TaskRequirement,
    TaskTeam,
    TaskStatus,
    TaskEvent,
    TaskRuntimeStep,
    TaskRuntime,
)
from .monitors import TaskMonitor, TaskMonitorManager
from .repositories import TaskRuntimeRepository
from .runnables import TaskRunnable
