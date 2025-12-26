from abc import ABC, abstractmethod
from typing import Optional, List

from fivcplayground.tasks.types.base import TaskRun, TaskRunStage


class TaskRuntimeRepository(ABC):
    """
    Abstract base class for task runtime data repositories.

    Defines the interface for persisting and retrieving task execution data.
    Implementations can use different storage backends (files, databases, etc.).

    Methods:
        update_task_runtime: Create or update a task's metadata
        get_task_runtime: Retrieve a task by ID
        delete_task_runtime: Delete a task and all its steps
        list_task_runtimes: List all tasks in the repository
        update_task_runtime_step: Create or update an execution step
        get_task_runtime_step: Retrieve a specific step by task ID and step ID
        list_task_runtime_steps: List all steps for a task
    """

    @abstractmethod
    def update_task_runtime(self, task: TaskRun) -> None:
        """Create or update a task's metadata."""
        ...

    @abstractmethod
    def get_task_runtime(self, task_id: str) -> Optional[TaskRun]:
        """Retrieve a task by ID."""
        ...

    @abstractmethod
    def delete_task_runtime(self, task_id: str) -> None:
        """Delete a task and all its steps."""
        ...

    @abstractmethod
    def list_task_runtimes(self) -> List[TaskRun]:
        """List all tasks in the repository."""
        ...

    @abstractmethod
    def get_task_runtime_step(
        self, task_id: str, step_id: str
    ) -> Optional[TaskRunStage]:
        """Retrieve a specific step by task ID and step ID."""
        ...

    @abstractmethod
    def update_task_runtime_step(self, task_id: str, step: TaskRunStage) -> None:
        """Create or update an execution step."""
        ...

    @abstractmethod
    def list_task_runtime_steps(self, task_id: str) -> List[TaskRunStage]:
        """List all steps for a task."""
        ...
