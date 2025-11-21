#!/usr/bin/env python3
"""
Simple example demonstrating TaskMonitorManager usage.

This example shows how to:
1. Create a TaskMonitorManager with persistence
2. Create and execute tasks
3. Query task status and events
4. Save and load task history
"""

import asyncio
import dotenv

from fivcplayground import tools
from fivcplayground.tasks.types import TaskMonitorManager
from fivcplayground.utils import OutputDir

dotenv.load_dotenv()


async def main():
    print("=" * 60)
    print("TaskMonitorManager Simple Example")
    print("=" * 60)

    # 1. Create TaskMonitorManager with persistence
    print("\n1️⃣ Creating TaskMonitorManager with persistence...")
    from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository

    output_dir = OutputDir().subdir('tasks')
    repo = FileTaskRuntimeRepository(output_dir=output_dir)
    manager = TaskMonitorManager(runtime_repo=repo)

    print(f"✅ TaskMonitorManager created")
    print(f"   Output directory: {output_dir}")
    print(f"   Repository: FileTaskRuntimeRepository")
    print(f"   Tasks will be saved in: {output_dir}/task_<task_id>/")

    # 2. Define the query
    print("\n2️⃣ Defining task query...")
    query = "Calculate 123 * 456"
    print(f"   Query: {query}")

    # 3. Create task with event callback
    print("\n3️⃣ Creating task with event tracking...")

    def on_runtime_update(runtime):
        """Callback function to track task runtime updates"""
        print(f"   📋 Task {runtime.id[:8]}: {runtime.status.value}")
        # Access latest steps from runtime
        if runtime.steps:
            latest_step = list(runtime.steps.values())[-1]
            print(f"      Latest step: {latest_step.agent_name} - {latest_step.status.value}")
            if latest_step.error:
                print(f"      ❌ Error: {latest_step.error}")

    swarm = await manager.create_task(
        query=query,
        tools_retriever=tools.create_tool_retriever(),
        on_event=on_runtime_update,
    )
    print("✅ Task created with step tracking")
    print("   (Planning was automatically executed)")

    # 4. Execute the task
    print("\n4️⃣ Executing task...")

    try:
        result = await swarm.run_async(query)
        print(f"\n✅ Task completed!")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"\n❌ Task failed: {e}")

    # 5. Query task information
    print("\n5️⃣ Querying task information...")
    tasks = manager.list_tasks()
    print(f"   Total tasks: {len(tasks)}")

    for task_runtime in tasks:
        print(f"\n   Task ID: {task_runtime.id}")

        # Get the task monitor to access steps
        task_monitor = manager.get_task(task_runtime.id)
        if task_monitor:
            steps = task_monitor.list_steps()
            print(f"   Total steps: {len(steps)}")

            for step in steps:
                print(f"\n   📊 Step Details:")
                print(f"      Agent: {step.agent_name}")
                print(f"      Status: {step.status.value}")
                if step.duration:
                    print(f"      Duration: {step.duration:.2f}s")

    # 6. Custom statistics
    print("\n6️⃣ Custom statistics...")
    total_steps = 0
    status_counts = {}

    for task_runtime in manager.list_tasks():
        task_monitor = manager.get_task(task_runtime.id)
        if task_monitor:
            for step in task_monitor.list_steps():
                total_steps += 1
                status = step.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

    print(f"   Total steps: {total_steps}")
    print(f"   By status:")
    for status, count in status_counts.items():
        print(f"      {status}: {count}")

    # 7. Task persistence
    print("\n7️⃣ Task persistence...")
    print(f"✅ Tasks are automatically persisted to disk")
    print(f"   Each task saved in: {output_dir}/task_<task_id>/")

    # List saved task directories
    import os
    task_dirs = [d for d in os.listdir(str(output_dir)) if d.startswith("task_")]
    print(f"   Found {len(task_dirs)} task directories:")
    for d in task_dirs[:3]:  # Show first 3
        print(f"      - {d}")
    if len(task_dirs) > 3:
        print(f"      ... and {len(task_dirs) - 3} more")

    # 8. Demonstrate loading
    print("\n8️⃣ Demonstrating load from repository...")
    new_repo = FileTaskRuntimeRepository(output_dir=output_dir)
    new_manager = TaskMonitorManager(runtime_repo=new_repo)
    print(f"✅ Automatically loaded {len(new_manager.list_tasks())} tasks")
    print(f"   Tasks are loaded from repository on demand")

    print("\n" + "=" * 60)
    print("Example completed successfully! 🎉")
    print("=" * 60)
    print("\n💡 Tip: Each task is saved in its own directory with task.json and steps/")
    print("💡 Tip: TaskMonitorManager uses FileTaskRuntimeRepository for persistence")
    print("💡 Tip: Tasks are automatically persisted when created with a repository")


if __name__ == "__main__":
    asyncio.run(main())
