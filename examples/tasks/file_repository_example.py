#!/usr/bin/env python3
"""
Example demonstrating FileTaskRuntimeRepository usage.

This example shows how to:
1. Create a TaskMonitor with file-based persistence
2. Persist task runtime data to disk
3. Reload task state from disk
4. List and manage multiple tasks
"""

from datetime import datetime
from fivcplayground.tasks.types import TaskMonitor, TaskRuntimeStep, TaskStatus
from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository
from fivcplayground.utils import OutputDir


def example_basic_persistence():
    """Basic example of persisting task data to files."""
    print("=" * 60)
    print("Example 1: Basic Persistence")
    print("=" * 60)
    
    # Create a repository with a specific output directory
    output_dir = OutputDir().subdir('tasks')
    repo = FileTaskRuntimeRepository(output_dir=output_dir)
    
    # Create a TaskMonitor with the repository
    monitor = TaskMonitor(runtime_repo=repo)
    print(f"Created task monitor with ID: {monitor.id}")
    
    # Add some steps (simulating agent execution)
    step1 = TaskRuntimeStep(
        id="agent-1",
        agent_name="PlanningAgent",
        status=TaskStatus.COMPLETED,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )
    
    step2 = TaskRuntimeStep(
        id="agent-2",
        agent_name="ExecutionAgent",
        status=TaskStatus.EXECUTING,
        started_at=datetime.now(),
    )
    
    monitor.steps[step1.id] = step1
    monitor.steps[step2.id] = step2
    
    # Persist all data to disk
    monitor.persist()
    print(f"Persisted task data to: {output_dir}")
    print(f"  - Task file: {repo._get_task_file(monitor.id)}")
    print(f"  - Steps directory: {repo._get_steps_dir(monitor.id)}")
    
    return monitor.id, output_dir


def example_reload_from_disk(task_id, output_dir):
    """Example of reloading task state from disk."""
    print("\n" + "=" * 60)
    print("Example 2: Reload from Disk")
    print("=" * 60)

    # Create a new repository instance
    repo = FileTaskRuntimeRepository(output_dir=output_dir)

    # Load the task from disk
    task_runtime = repo.get_task_runtime(task_id)
    if task_runtime:
        print(f"Loaded task: {task_runtime.id}")
        print(f"  Status: {task_runtime.status}")

        # Create a new monitor with the loaded runtime
        monitor = TaskMonitor(runtime=task_runtime, runtime_repo=repo)

        # List all steps
        steps = monitor.list_steps()
        print(f"  Steps: {len(steps)}")
        for step in steps:
            print(f"    - {step.agent_name} ({step.id}): {step.status}")
    else:
        print(f"Task {task_id} not found")


def example_list_all_tasks():
    """Example of listing all tasks in the repository."""
    print("\n" + "=" * 60)
    print("Example 3: List All Tasks")
    print("=" * 60)
    
    output_dir = OutputDir().subdir('tasks')
    repo = FileTaskRuntimeRepository(output_dir=output_dir)
    
    # Create a few more tasks
    for i in range(3):
        monitor = TaskMonitor(runtime_repo=repo)
        step = TaskRuntimeStep(
            id=f"agent-{i}",
            agent_name=f"Agent{i}",
            status=TaskStatus.COMPLETED if i % 2 == 0 else TaskStatus.EXECUTING,
        )
        monitor.steps[step.id] = step
        monitor.persist()
        print(f"Created task {i+1}: {monitor.id}")
    
    # List all tasks
    print("\nAll tasks in repository:")
    tasks = repo.list_task_runtimes()
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. Task {task.id}")
        print(f"     Status: {task.status}")

        # List steps for this task
        steps = repo.list_task_runtime_steps(task.id)
        print(f"     Steps: {len(steps)}")


def example_cleanup():
    """Example of cleaning up task data."""
    print("\n" + "=" * 60)
    print("Example 4: Cleanup")
    print("=" * 60)

    output_dir = OutputDir().subdir('tasks')
    repo = FileTaskRuntimeRepository(output_dir=output_dir)

    # List tasks before cleanup
    tasks_before = repo.list_task_runtimes()
    print(f"Tasks before cleanup: {len(tasks_before)}")

    # Delete the first task
    if tasks_before:
        task_to_delete = tasks_before[0]
        print(f"Deleting task: {task_to_delete.id}")
        repo.delete_task_runtime(task_to_delete.id)

    # List tasks after cleanup
    tasks_after = repo.list_task_runtimes()
    print(f"Tasks after cleanup: {len(tasks_after)}")

    # Clean up all remaining tasks
    print("\nCleaning up all remaining tasks...")
    for task in tasks_after:
        repo.delete_task_runtime(task.id)

    # Verify cleanup
    final_tasks = repo.list_task_runtimes()
    print(f"Final task count: {len(final_tasks)}")

    # Clean up the output directory
    output_dir.cleanup()
    print(f"Removed output directory: {output_dir}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("FileTaskRuntimeRepository Examples")
    print("=" * 60)
    
    # Example 1: Basic persistence
    task_id, output_dir = example_basic_persistence()
    
    # Example 2: Reload from disk
    example_reload_from_disk(task_id, output_dir)
    
    # Example 3: List all tasks
    example_list_all_tasks()
    
    # Example 4: Cleanup
    example_cleanup()
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

