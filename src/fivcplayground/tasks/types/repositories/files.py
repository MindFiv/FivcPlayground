"""
File-based task repository implementations.

This module provides file-based implementations of task repositories:
- FileTaskPlanRepository: Stores task plans in JSON files
- FileTaskRunRepository: Stores task run data in JSON files

Storage Structure:
    /<output_dir>/
    ├── task_plans/
    │   └── <task_plan_id>.json    # Task plan data
    └── task_<task_id>/
        ├── task.json              # Task metadata

This structure allows for:
    - Easy inspection of task data
    - Simple backup and version control
    - Human-readable JSON format
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List

from fivcplayground.utils import OutputDir
from fivcplayground.tasks.types.repositories import (
    TaskPlan,
    TaskPlanRepository,
    TaskRun,
    TaskRunRepository,
)


class FileTaskPlanRepository(TaskPlanRepository):
    """
    File-based repository for task plan data.

    Storage structure:
    /<output_dir>/
    └── task_plans/
        └── <task_plan_id>.json    # Task plan data
    """

    def __init__(self, output_dir: Optional[OutputDir] = None):
        self.output_dir = output_dir or OutputDir().subdir("tasks")
        self.base_path = Path(str(self.output_dir))
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.plans_dir = self.base_path / "task_plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

    def _get_task_plan_file(self, task_plan_id: str) -> Path:
        """Get the file path for a task plan."""
        return self.plans_dir / f"{task_plan_id}.json"

    async def update_task_plan_async(self, task_plan: TaskPlan) -> None:
        """
        Create or update a task plan.

        Args:
            task_plan: TaskPlan instance to persist
        """
        task_plan_file = self._get_task_plan_file(task_plan.id)

        # Serialize task plan to JSON
        task_plan_data = task_plan.model_dump(mode="json")

        with open(task_plan_file, "w", encoding="utf-8") as f:
            json.dump(task_plan_data, f, indent=2, ensure_ascii=False)

    async def get_task_plan_async(self, task_plan_id: str) -> Optional[TaskPlan]:
        """
        Retrieve a task plan by ID.

        Args:
            task_plan_id: Task plan ID to retrieve

        Returns:
            TaskPlan instance or None if not found
        """
        task_plan_file = self._get_task_plan_file(task_plan_id)

        if not task_plan_file.exists():
            return None

        try:
            with open(task_plan_file, "r", encoding="utf-8") as f:
                task_plan_data = json.load(f)

            # Reconstruct TaskPlan from JSON
            return TaskPlan.model_validate(task_plan_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(f"Error loading task plan {task_plan_id}: {e}")
            return None

    async def delete_task_plan_async(self, task_plan_id: str) -> None:
        """
        Delete a task plan.

        Args:
            task_plan_id: Task plan ID to delete
        """
        task_plan_file = self._get_task_plan_file(task_plan_id)

        if task_plan_file.exists():
            task_plan_file.unlink()

    async def list_task_plans_async(self) -> List[TaskPlan]:
        """
        List all task plans.

        Returns:
            List of TaskPlan instances
        """
        task_plans = []

        # Iterate through all task plan files
        for task_plan_file in self.plans_dir.glob("*.json"):
            if not task_plan_file.is_file():
                continue

            # Extract task_plan_id from filename
            task_plan_id = task_plan_file.stem

            # Load task plan
            task_plan = await self.get_task_plan_async(task_plan_id)
            if task_plan:
                task_plans.append(task_plan)

        return task_plans


class FileTaskRunRepository(TaskRunRepository):
    """
    File-based repository for task run data.

    Storage structure:
    /<output_dir>/
    └── task_<task_id>/
        ├── task.json              # Task metadata
    """

    def __init__(self, output_dir: Optional[OutputDir] = None):
        self.output_dir = output_dir or OutputDir().subdir("tasks")
        self.base_path = Path(str(self.output_dir))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_task_dir(self, task_id: str) -> Path:
        """Get the directory path for a task."""
        return self.base_path / f"task_{task_id}"

    def _get_task_file(self, task_id: str) -> Path:
        """Get the file path for task metadata."""
        return self._get_task_dir(task_id) / "task.json"

    async def update_task_run_async(self, task: TaskRun) -> None:
        """
        Create or update a task.

        Args:
            task: TaskRun instance to persist
        """
        task_dir = self._get_task_dir(str(task.id))
        task_dir.mkdir(parents=True, exist_ok=True)

        task_file = self._get_task_file(str(task.id))

        # Serialize task to JSON (exclude steps as they're stored separately)
        task_data = task.model_dump(mode="json", exclude={"steps"})

        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)

    async def get_task_run_async(self, task_id: str) -> Optional[TaskRun]:
        """
        Retrieve a task by ID.

        Args:
            task_id: Task ID to retrieve

        Returns:
            TaskRun instance or None if not found
        """
        task_file = self._get_task_file(task_id)

        if not task_file.exists():
            return None

        try:
            with open(task_file, "r", encoding="utf-8") as f:
                task_data = json.load(f)

            # Reconstruct TaskRun from JSON
            return TaskRun.model_validate(task_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(f"Error loading task {task_id}: {e}")
            return None

    async def delete_task_run_async(self, task_id: str) -> None:
        """
        Delete a task and all its steps.

        Args:
            task_id: Task ID to delete
        """
        task_dir = self._get_task_dir(task_id)

        if task_dir.exists():
            shutil.rmtree(task_dir)

    async def list_task_runs_async(self) -> List[TaskRun]:
        """
        List all tasks.

        Returns:
            List of TaskRun instances
        """
        tasks = []

        # Iterate through all task directories
        for task_dir in self.base_path.glob("task_*"):
            if not task_dir.is_dir():
                continue

            # Extract task_id from directory name
            task_id = task_dir.name.replace("task_", "")

            # Load task
            task = await self.get_task_run_async(task_id)
            if task:
                tasks.append(task)

        return tasks
