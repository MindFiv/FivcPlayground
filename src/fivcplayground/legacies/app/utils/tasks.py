"""
Task manager for UI layer.

This module provides TaskManager class to coordinate task execution
with UI notifications and state management.

TaskManager wraps TaskMonitorManager from the core tasks module and adds
UI-specific functionality like notifications to Chat. It uses the
new TaskMonitorManager.create_task() API which handles planning internally.
"""

import asyncio
from typing import Optional, List, Callable

from fivcplayground import tools
from fivcplayground.tasks.types import (
    TaskStatus,
    TaskRuntime,
    TaskMonitor,
    TaskMonitorManager,
)


class TaskManager(object):
    """
    Manages tasks for the UI layer with notifications and state management.

    This is a UI-layer wrapper around TaskMonitorManager that adds:
    - Automatic task execution in background
    - Completion notifications to Chat
    - Simplified task creation API for UI

    The underlying TaskMonitorManager.create_task() handles:
    - Planning via create_planning_task()
    - TaskMonitor creation with persistence
    - Agent swarm creation with monitoring hooks

    Attributes:
        monitor_manager: Core TaskMonitorManager instance
    """

    def __init__(
        self,
        monitor_manager: TaskMonitorManager,
        on_task_complete: Optional[Callable[[TaskRuntime], None]] = None,
    ):
        """
        Initialize TaskManager.

        Args:
            monitor_manager: Core TaskMonitorManager instance
            on_task_complete: Optional callback for task completion notifications
        """
        self.monitor_manager = monitor_manager
        self.on_task_complete = on_task_complete

    def _on_task_event(self, runtime: TaskRuntime) -> None:
        """
        Callback for task runtime updates.
        """
        if self.on_task_complete and runtime.is_completed:
            self.on_task_complete(runtime)

    async def create_task(
        self,
        query: str,
        tools_retriever: Optional[tools.ToolsRetriever] = None,
    ) -> None:
        """
        Create and execute a task from a user query.

        This uses TaskMonitorManager.create_task() which handles:
        1. Planning (via create_planning_task)
        2. Creating TaskMonitor with persistence
        3. Creating agent swarm with monitoring hooks

        Args:
            query: User query to process
            tools_retriever: Optional tools retriever (defaults to default_retriever)

        Returns:
            Task ID of the created task

        Raises:
            Exception: If task creation or execution fails
        """
        assert tools_retriever is not None

        # Create task with monitoring (planning is done internally)
        task = await self.monitor_manager.create_task(
            query=query,
            tools_retriever=tools_retriever,
            on_event=self._on_task_event,
        )
        # Execute the task asynchronously (fire and forget)
        asyncio.create_task(task.invoke_async(query))

    def list_running_tasks(self) -> List[TaskMonitor]:
        """
        Get all currently running tasks.

        Returns:
            List of TaskMonitor instances for running tasks
        """
        return self.monitor_manager.list_tasks(status=[TaskStatus.EXECUTING])

    def list_completed_tasks(self) -> List[TaskMonitor]:
        """
        Get all completed tasks (both successful and failed).

        Returns:
            List of TaskMonitor instances for completed tasks
        """
        return self.monitor_manager.list_tasks(status=[TaskStatus.COMPLETED])

    def list_failed_tasks(self) -> List[TaskMonitor]:
        """
        Get all failed tasks.

        Returns:
            List of TaskMonitor instances for failed tasks
        """
        return self.monitor_manager.list_tasks(status=[TaskStatus.FAILED])

    def get_task(self, task_id: str) -> Optional[TaskMonitor]:
        """
        Get a specific task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            TaskMonitor instance or None if not found
        """
        return self.monitor_manager.get_task(task_id)

    def delete_task(self, task_id: str) -> None:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete
        """
        self.monitor_manager.delete_task(task_id)
