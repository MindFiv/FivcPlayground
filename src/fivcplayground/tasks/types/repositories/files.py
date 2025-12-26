"""
File-based task runtime repository implementation.

This module provides FileTaskRuntimeRepository, a file-based implementation
of TaskRuntimeRepository that stores task data in a hierarchical directory
structure with JSON files.

Storage Structure:
    /<output_dir>/
    └── task_<task_id>/
        ├── task.json              # Task metadata
        └── steps/
            ├── step_<step_id>.json
            └── step_<step_id>.json

This structure allows for:
    - Easy inspection of task data
    - Efficient step-by-step updates
    - Simple backup and version control
    - Human-readable JSON format
"""

import json
import shutil
from pathlib import Path
from typing import Optional, List

from fivcplayground.utils import OutputDir
from fivcplayground.tasks.types.repositories import (
    TaskRun,
    TaskRunStage,
    TaskRuntimeRepository,
)


class FileTaskRuntimeRepository(TaskRuntimeRepository):
    """
    File-based repository for task runtime data.

    Storage structure:
    /<output_dir>/
    └── task_<task_id>/
        ├── task.json              # Task metadata
        └── steps/
            ├── step_<step_id>.json
            └── step_<step_id>.json
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

    def _get_steps_dir(self, task_id: str) -> Path:
        """Get the directory path for task steps."""
        return self._get_task_dir(task_id) / "steps"

    def _get_step_file(self, task_id: str, step_id: str) -> Path:
        """Get the file path for a step."""
        return self._get_steps_dir(task_id) / f"step_{step_id}.json"

    def update_task_runtime(self, task: TaskRun) -> None:
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

    def get_task_runtime(self, task_id: str) -> Optional[TaskRun]:
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
            # Note: steps are loaded separately via list_task_runtime_steps
            return TaskRun.model_validate(task_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(f"Error loading task {task_id}: {e}")
            return None

    def delete_task_runtime(self, task_id: str) -> None:
        """
        Delete a task and all its steps.

        Args:
            task_id: Task ID to delete
        """
        task_dir = self._get_task_dir(task_id)

        if task_dir.exists():
            shutil.rmtree(task_dir)

    def list_task_runtimes(self) -> List[TaskRun]:
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
            task = self.get_task_runtime(task_id)
            if task:
                tasks.append(task)

        return tasks

    def get_task_runtime_step(
        self, task_id: str, step_id: str
    ) -> Optional[TaskRunStage]:
        """
        Retrieve a step by task ID and step ID.

        Args:
            task_id: Task ID
            step_id: Step ID

        Returns:
            TaskRunStage instance or None if not found
        """
        step_file = self._get_step_file(task_id, step_id)

        if not step_file.exists():
            return None

        try:
            with open(step_file, "r", encoding="utf-8") as f:
                step_data = json.load(f)

            # Reconstruct TaskRunStage from JSON
            return TaskRunStage.model_validate(step_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Log error and return None if file is corrupted
            print(f"Error loading step {step_id} for task {task_id}: {e}")
            return None

    def update_task_runtime_step(self, task_id: str, step: TaskRunStage) -> None:
        """
        Create or update a step.

        Args:
            task_id: Task ID
            step: TaskRunStage instance to persist
        """
        steps_dir = self._get_steps_dir(task_id)
        steps_dir.mkdir(parents=True, exist_ok=True)

        step_file = self._get_step_file(task_id, step.id)

        # Serialize step to JSON
        step_data = step.model_dump(mode="json")

        with open(step_file, "w", encoding="utf-8") as f:
            json.dump(step_data, f, indent=2, ensure_ascii=False)

    def list_task_runtime_steps(self, task_id: str) -> List[TaskRunStage]:
        """
        List all steps for a task.

        Args:
            task_id: Task ID

        Returns:
            List of TaskRunStage instances
        """
        steps = []
        steps_dir = self._get_steps_dir(task_id)

        if not steps_dir.exists():
            return steps

        # Iterate through all step files
        for step_file in steps_dir.glob("step_*.json"):
            if not step_file.is_file():
                continue

            # Extract step_id from file name
            step_id = step_file.stem.replace("step_", "")

            # Load step
            step = self.get_task_runtime_step(task_id, step_id)
            if step:
                steps.append(step)

        return steps
