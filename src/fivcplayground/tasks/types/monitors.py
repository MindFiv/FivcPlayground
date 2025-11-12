"""
Task execution monitor using Strands hooks.

This module provides TaskMonitor class for tracking Agent and MultiAgent execution state
through Strands' hook system. TaskMonitor requires a TaskRuntimeRepository for persisting
execution data.

This module also provides TaskMonitorManager class for managing and monitoring multiple tasks
across different agent swarms. TaskMonitorManager uses TaskRuntimeRepository for persistence
and TaskMonitor for tracking individual task execution.

Key Features:
    - Hook-based execution tracking (recommended)
    - Required persistence through repository pattern
    - Real-time step updates via callbacks
    - Automatic task and step lifecycle management
    - Centralized task lifecycle management through TaskMonitorManager
    - Automatic planning integration in TaskMonitorManager
"""

from functools import cached_property
from typing import Any, Optional, List, Callable, Dict

from fivcplayground import agents, tools
from fivcplayground.tasks.types.base import (
    TaskTeam,
    TaskStatus,
    TaskRuntime,
    TaskRuntimeStep,
)
from fivcplayground.tasks.types.repositories import TaskRuntimeRepository


class TaskMonitor(object):
    """
    Task execution monitor using Strands hooks.

    Tracks Agent or MultiAgent execution state through hook events and persists
    execution data through a required TaskRuntimeRepository.

    Usage with hooks (recommended):
        >>> from fivcplayground.tasks.types import TaskMonitor
        >>> from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository
        >>> from fivcplayground import agents
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> # Create repository and monitor
        >>> repo = FileTaskRuntimeRepository(output_dir=OutputDir("./tasks"))
        >>> monitor = TaskMonitor(runtime_repo=repo)
        >>>
        >>> # Create agent swarm with monitor as hook
        >>> plan = TaskTeam(specialists=[...])
        >>> swarm = agents.create_generic_agent_swarm(
        ...     team=plan,
        ...     hooks=[monitor]
        ... )
        >>>
        >>> # Execute and monitor automatically tracks execution
        >>> result = await swarm.invoke_async("Your query")
        >>>
        >>> # Access execution steps
        >>> steps = monitor.list_steps()
        >>> for step in steps:
        ...     print(f"{step.agent_name}: {step.status}")

    Usage with persistence:
        >>> from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> # Create repository
        >>> repo = FileTaskRuntimeRepository(output_dir=OutputDir("./tasks"))
        >>>
        >>> # Create monitor with persistence
        >>> monitor = TaskMonitor(runtime_repo=repo)
        >>>
        >>> # Task and steps are automatically persisted to disk
        >>> # Can be reloaded later
        >>> loaded_task = repo.get_task_runtime(monitor.id)
        >>> loaded_monitor = TaskMonitor(runtime=loaded_task, runtime_repo=repo)

    Event callbacks:
        You can register callbacks to be notified of task events:
        >>> from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> def on_event(runtime: TaskRuntime):
        ...     print(f"Task {runtime.id}: {runtime.status}")
        ...     # Access latest step information from runtime.steps
        >>>
        >>> repo = FileTaskRuntimeRepository(output_dir=OutputDir("./tasks"))
        >>> monitor = TaskMonitor(on_event=on_event, runtime_repo=repo)
    """

    @property
    def id(self) -> str:
        return self._runtime.id

    @property
    def query(self) -> str:
        return self._runtime.query

    @property
    def team(self) -> Optional[TaskTeam]:
        return self._runtime.team

    @property
    def status(self) -> TaskStatus:
        return self._runtime.status

    @cached_property
    def steps(self) -> Dict[str, TaskRuntimeStep]:
        if not self._runtime.steps:
            steps = self._repo.list_task_runtime_steps(self.id)
            self._runtime.steps = {step.id: step for step in steps}
        return self._runtime.steps

    def __init__(
        self,
        on_event: Optional[Callable[[TaskRuntime], None]] = None,
        runtime: Optional[TaskRuntime] = None,
        runtime_repo: Optional[TaskRuntimeRepository] = None,
    ):
        """
        Initialize TaskMonitor.

        Args:
            on_event: Optional callback invoked when task events occur (step state changes, etc.)
            runtime: Optional existing TaskRuntime to monitor (for loading saved tasks)
            runtime_repo: Required repository for persisting task data

        Raises:
            AssertionError: If runtime_repo is None

        Note:
            runtime_repo is required for all TaskMonitor instances. If runtime is not
            provided, a new TaskRuntime will be created and persisted.
        """
        assert runtime_repo is not None

        self._runtime = runtime or TaskRuntime()
        self._repo = runtime_repo
        self._on_event = on_event

        if not runtime:
            self._repo.update_task_runtime(self._runtime)

    def get_step(self, agent_id: str) -> Optional[TaskRuntimeStep]:
        """
        Get execution step for a specific agent.

        Args:
            agent_id: Agent ID (same as step ID) to retrieve

        Returns:
            TaskRuntimeStep for the agent, or None if not found
        """
        return self.steps.get(agent_id)

    def list_steps(self) -> List[TaskRuntimeStep]:
        """
        Get all execution steps for this task.

        Returns:
            List of all TaskRuntimeStep instances
        """
        return list(self.steps.values())

    def cleanup(self) -> None:
        """
        Clean up task data.
        """
        # Clean up all steps and task

        self._repo.delete_task_runtime(self.id)
        self._runtime.cleanup()

    def persist(self) -> None:
        """
        Manually persist task and all steps to the repository.

        This is useful when you want to ensure data is saved immediately.
        Note: Steps are automatically persisted when using hooks, so this
        is typically only needed when using the deprecated __call__ method.
        """
        self._repo.update_task_runtime(self._runtime)

        for step in self.steps.values():
            self._repo.update_task_runtime_step(self.id, step)


class TaskMonitorManager(object):
    """
    Centralized task monitor manager for monitoring and managing task execution.

    TaskMonitorManager provides a unified interface to:
    - Create and track tasks with agent swarms
    - Monitor task execution status through TaskMonitor
    - Persist task history through TaskRuntimeRepository

    Usage:
        >>> from fivcplayground.tasks.types.monitors import TaskMonitorManager
        >>> from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository
        >>> from fivcplayground import tools
        >>> from fivcplayground.utils import OutputDir
        >>>
        >>> # Create manager with file-based persistence
        >>> repo = FileTaskRuntimeRepository(output_dir=OutputDir("./tasks"))
        >>> manager = TaskMonitorManager(runtime_repo=repo)
        >>>
        >>> # Create a task with monitoring (planning is done automatically)
        >>> swarm = await manager.create_task(
        ...     query="Your query here",
        ...     tools_retriever=tools.default_retriever
        ... )
        >>>
        >>> # Execute task (automatically tracked and persisted)
        >>> result = await swarm.invoke_async("Your query")
        >>>
        >>> # View all tasks
        >>> tasks = manager.list_tasks()  # Returns list of TaskRuntime
        >>>
        >>> # Get specific task with monitor
        >>> task_monitor = manager.get_task(task_id)
        >>> steps = task_monitor.list_steps()
        >>>
        >>> # Delete a task
        >>> manager.delete_task(task_id)
    """

    def __init__(
        self, runtime_repo: Optional["TaskRuntimeRepository"] = None, **kwargs
    ):
        assert runtime_repo is not None

        self._repo = runtime_repo

    async def create_task(
        self,
        query: str,
        tools_retriever: Optional["tools.ToolsRetriever"] = None,
        on_event: Optional[Callable[[TaskRuntime], None]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Create a new task with agent swarm and monitor.

        Args:
            query: User query to process
            tools_retriever: Optional tools retriever for agent tools
            on_event: Optional callback invoked with TaskRuntime after each task event
            **kwargs: Additional arguments to pass to the swarm

        Returns:
            Agent swarm instance
        """
        # Import here to avoid circular dependency
        from fivcplayground.tasks import create_planning_task

        task_team = create_planning_task(
            query,
            tools_retriever=tools_retriever,
            **kwargs,
        )
        task_team = await task_team.run_async()
        task_runtime = TaskRuntime(
            query=query,
            team=task_team,
        )
        task_monitor = TaskMonitor(
            on_event=on_event,
            runtime=task_runtime,
            runtime_repo=self._repo,
        )
        task = agents.create_generic_agent_swarm(
            team=task_team,
            tools_retriever=tools_retriever,
            hooks=[task_monitor],
            **kwargs,
        )
        self._repo.update_task_runtime(task_runtime)

        return task

    def list_tasks(
        self, status: Optional[List[TaskStatus]] = None
    ) -> List[TaskMonitor]:
        """
        Get list of all task monitors.

        Returns:
            List of TaskMonitor instances
        """
        task_runtimes = self._repo.list_task_runtimes()
        if status:
            return [
                TaskMonitor(runtime=runtime, runtime_repo=self._repo)
                for runtime in task_runtimes
                if runtime.status in status
            ]

        else:
            return [
                TaskMonitor(runtime=runtime, runtime_repo=self._repo)
                for runtime in task_runtimes
            ]

    def get_task(
        self, task_id: str, on_event: Optional[Callable[[TaskRuntime], None]] = None
    ) -> Optional[TaskMonitor]:
        """
        Get a task monitor by ID.

        Args:
            task_id: Task ID to retrieve
            on_event: Optional callback invoked with TaskRuntime after each task event

        Returns:
            TaskMonitor instance or None if not found
        """
        task_runtime = self._repo.get_task_runtime(task_id)
        if not task_runtime:
            return None

        return TaskMonitor(
            runtime=task_runtime,
            runtime_repo=self._repo,
            on_event=on_event,
        )

    def delete_task(self, task_id: str) -> None:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete
        """
        self._repo.delete_task_runtime(task_id)
