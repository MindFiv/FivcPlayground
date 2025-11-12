#!/usr/bin/env python3
"""
Tests for TaskMonitor functionality.
"""

import tempfile
from unittest.mock import Mock
from datetime import datetime

from fivcplayground.tasks.types import TaskMonitor, TaskRuntimeStep, TaskStatus
from fivcplayground.tasks.types.repositories.files import FileTaskRuntimeRepository
from fivcplayground.utils import OutputDir


class TestTaskTrace:
    """Tests for TaskRuntimeStep class"""

    def test_initialization(self):
        """Test TaskRuntimeStep initialization"""
        event = TaskRuntimeStep(
            id="test-123",
            agent_name="TestAgent",
        )

        assert event.agent_name == "TestAgent"
        assert event.id == "test-123"
        assert event.agent_id == "test-123"  # computed field
        assert event.status == TaskStatus.PENDING
        assert event.started_at is None
        assert event.completed_at is None
        assert event.messages == []
        assert event.error is None

    def test_duration_calculation(self):
        """Test duration calculation"""
        event = TaskRuntimeStep(agent_name="TestAgent")

        # No duration when not started
        assert event.duration is None

        # Set start and end times
        event.started_at = datetime(2024, 1, 1, 12, 0, 0)
        event.completed_at = datetime(2024, 1, 1, 12, 0, 5)

        # Should calculate 5 seconds
        assert event.duration == 5.0

    def test_is_running(self):
        """Test is_running property"""
        event = TaskRuntimeStep(agent_name="TestAgent")

        assert not event.is_running

        event.status = TaskStatus.EXECUTING
        assert event.is_running

        event.status = TaskStatus.COMPLETED
        assert not event.is_running

    def test_is_completed(self):
        """Test is_completed property"""
        event = TaskRuntimeStep(agent_name="TestAgent")

        assert not event.is_completed

        event.status = TaskStatus.EXECUTING
        assert not event.is_completed

        event.status = TaskStatus.COMPLETED
        assert event.is_completed

        event.status = TaskStatus.FAILED
        assert event.is_completed

    def test_model_dump(self):
        """Test Pydantic model_dump"""
        event = TaskRuntimeStep(
            id="test-123",
            agent_name="TestAgent",
        )
        event.status = TaskStatus.EXECUTING
        event.started_at = datetime(2024, 1, 1, 12, 0, 0)
        from langchain_core.messages import HumanMessage

        event.messages.append(HumanMessage(content="test"))

        # Test with messages included (default)
        result = event.model_dump(mode="json")

        assert result["agent_name"] == "TestAgent"
        assert result["id"] == "test-123"
        assert result["agent_id"] == "test-123"  # computed field
        assert result["status"] == "executing"  # TaskStatus.EXECUTING value
        assert result["started_at"] == "2024-01-01T12:00:00"
        assert "messages" in result
        assert len(result["messages"]) == 1

        # Test without messages (compact mode)
        result_compact = event.model_dump(mode="json", exclude={"messages"})
        assert "messages" not in result_compact


class TestTaskMonitor:
    """Tests for TaskMonitor class"""

    def test_initialization(self):
        """Test TaskMonitor initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)
            monitor = TaskMonitor(runtime_repo=repo)

            assert monitor._on_event is None
            assert monitor.list_steps() == []

    def test_initialization_with_callbacks(self):
        """Test TaskMonitor initialization with callbacks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileTaskRuntimeRepository(output_dir=output_dir)
            on_event = Mock()

            monitor = TaskMonitor(on_event=on_event, runtime_repo=repo)

            assert monitor._on_event == on_event
