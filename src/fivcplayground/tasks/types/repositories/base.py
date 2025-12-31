from abc import ABC, abstractmethod
from typing import Optional, List

from fivcplayground.tasks.types.base import TaskRun


class TaskRunRepository(ABC):
    """
    Abstract base class for task run data repositories.

    Defines the interface for persisting and retrieving task execution data.
    Implementations can use different storage backends (files, databases, etc.).

    Methods:
        update_task_run_async: Create or update a task's metadata
        get_task_run_async: Retrieve a task by ID
        delete_task_run_async: Delete a task and all its steps
        list_task_runs_async: List all tasks in the repository
    """

    @abstractmethod
    async def update_task_run_async(self, task: TaskRun) -> None:
        """Create or update a task's metadata."""
        ...

    @abstractmethod
    async def get_task_run_async(self, task_id: str) -> Optional[TaskRun]:
        """Retrieve a task by ID."""
        ...

    @abstractmethod
    async def delete_task_run_async(self, task_id: str) -> None:
        """Delete a task and all its steps."""
        ...

    @abstractmethod
    async def list_task_runs_async(self) -> List[TaskRun]:
        """List all tasks in the repository."""
        ...
