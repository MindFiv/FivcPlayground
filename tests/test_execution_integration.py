#!/usr/bin/env python3
"""
Integration tests for task workflow

Tests the complete workflow integration without requiring actual LLM calls.
"""

import sys
import dotenv

from fivcplayground import tasks, agents

dotenv.load_dotenv()


class TestExecutionTaskIntegration:
    """Integration tests for execution task"""

    def test_imports(self):
        """Test that all required imports work"""
        assert hasattr(tasks, "create_planning_task")
        assert hasattr(tasks, "create_assessing_task")
        assert hasattr(tasks, "TaskTeam")
        assert hasattr(tasks, "TaskMonitor")
        assert hasattr(tasks, "TaskRuntimeStep")
        assert hasattr(tasks, "TaskStatus")

    def test_task_team_creation(self):
        """Test creating a TaskTeam"""
        team = tasks.TaskTeam(
            specialists=[
                tasks.TaskTeam.Specialist(
                    name="Researcher",
                    backstory="Expert researcher",
                    tools=["web_search"],
                ),
                tasks.TaskTeam.Specialist(
                    name="Analyst", backstory="Expert analyst", tools=["calculator"]
                ),
            ]
        )

        assert len(team.specialists) == 2
        assert team.specialists[0].name == "Researcher"
        assert team.specialists[1].name == "Analyst"
        assert "web_search" in team.specialists[0].tools
        assert "calculator" in team.specialists[1].tools

    def test_task_event_tracking(self):
        """Test TaskRuntimeStep tracking"""
        from datetime import datetime

        # Create task event
        event = tasks.TaskRuntimeStep(agent_name="TestAgent", agent_id="test-123")

        assert event.status == tasks.TaskStatus.PENDING
        assert event.agent_name == "TestAgent"

        # Update status
        event.status = tasks.TaskStatus.EXECUTING
        event.started_at = datetime.now()

        assert event.status == tasks.TaskStatus.EXECUTING
        assert event.started_at is not None
        assert event.is_running

        # Complete
        event.status = tasks.TaskStatus.COMPLETED
        event.completed_at = datetime.now()

        assert event.status == tasks.TaskStatus.COMPLETED
        assert event.is_completed
        assert event.duration is not None

    def test_create_planning_task_signature(self):
        """Test create_planning_task function signature"""
        import inspect

        sig = inspect.signature(tasks.create_planning_task)
        params = list(sig.parameters.keys())

        assert "query" in params
        assert "tools_retriever" in params
        assert "kwargs" in params

        # Check it's callable and returns a Runnable
        task = tasks.create_planning_task("Test query")
        assert hasattr(task, "run")
        assert hasattr(task, "run_async")

    def test_workflow_components(self):
        """Test that all workflow components exist"""
        # Assessment
        assert hasattr(tasks, "create_assessing_task")
        assert callable(tasks.create_assessing_task)

        # Planning
        assert hasattr(tasks, "create_planning_task")
        assert callable(tasks.create_planning_task)

        # Task execution through TaskMonitorManager
        assert hasattr(tasks, "TaskMonitorManager")
        assert callable(tasks.TaskMonitorManager)

        # Task schemas
        assert hasattr(tasks, "TaskAssessment")
        assert hasattr(tasks, "TaskRequirement")
        assert hasattr(tasks, "TaskTeam")

        # Task tracking
        assert hasattr(tasks, "TaskMonitor")
        assert hasattr(tasks, "TaskRuntimeStep")
        assert hasattr(tasks, "TaskStatus")

    def test_exports(self):
        """Test that functions are properly exported"""
        # Tasks module
        assert "create_planning_task" in tasks.__all__
        assert "create_assessing_task" in tasks.__all__
        assert "TaskMonitorManager" in tasks.__all__

        # Agents module
        assert "create_default_agent" in agents.__all__


def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Integration Tests")
    print("=" * 60)

    test_suite = TestExecutionTaskIntegration()

    tests = [
        ("Imports", test_suite.test_imports),
        ("TaskTeam Creation", test_suite.test_task_team_creation),
        ("Workflow Components", test_suite.test_workflow_components),
        ("Exports", test_suite.test_exports),
    ]

    results = []

    for name, test_func in tests:
        try:
            print(f"\n{'=' * 60}")
            print(f"Test: {name}")
            print(f"{'=' * 60}")

            test_func()

            print("✅ PASSED")
            results.append((name, True, None))

        except Exception as e:
            print(f"❌ FAILED: {e}")
            results.append((name, False, str(e)))

    # Print summary
    print(f"\n{'=' * 60}")
    print("Test Summary")
    print(f"{'=' * 60}")

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for name, success, error in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name}: {status}")
        if error:
            print(f"   Error: {error}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'=' * 60}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_tests())
