#!/usr/bin/env python3
"""
Tests for SimpleTaskRunnable.

Tests the SimpleTaskRunnable wrapper class that applies query templates
to agent runnables.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from pydantic import BaseModel

from fivcplayground.tasks.types.runnables import SimpleTaskRunnable
from fivcplayground.agents import AgentRunnable


class MockResponse(BaseModel):
    """Mock response model for testing."""

    result: str


class TestSimpleTaskRunnable:
    """Tests for SimpleTaskRunnable class."""

    def test_init(self):
        """Test SimpleTaskRunnable initialization."""
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.id = "test-agent"
        mock_runnable.name = "Test Agent"
        mock_runnable.description = "A test agent"

        task = SimpleTaskRunnable(
            runnable=mock_runnable,
            query_template="Process: {query}",
        )

        assert task._runnable == mock_runnable
        assert task._query == "Process: {query}"
        assert task._kwargs == {}

    def test_init_with_kwargs(self):
        """Test SimpleTaskRunnable initialization with kwargs."""
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.id = "test-agent"

        task = SimpleTaskRunnable(
            runnable=mock_runnable,
            query_template="Process: {query}",
            response_model=MockResponse,
            custom_param="value",
        )

        assert task._kwargs == {
            "response_model": MockResponse,
            "custom_param": "value",
        }

    def test_id_property(self):
        """Test id property delegation."""
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.id = "test-agent-123"

        task = SimpleTaskRunnable(mock_runnable)
        assert task.id == "test-agent-123"

    def test_name_property(self):
        """Test name property delegation."""
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.name = "Test Agent Name"

        task = SimpleTaskRunnable(mock_runnable)
        assert task.name == "Test Agent Name"

    def test_description_property(self):
        """Test description property delegation."""
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.description = "Test description"

        task = SimpleTaskRunnable(mock_runnable)
        assert task.description == "Test description"

    def test_run_with_query_template(self):
        """Test run method applies query template."""
        mock_response = MockResponse(result="processed")
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.id = "test-agent"
        mock_runnable.run = Mock(return_value=mock_response)

        task = SimpleTaskRunnable(
            runnable=mock_runnable,
            query_template="Analyze: {query}",
        )

        result = task.run(query="test input")

        # Verify the template was applied
        mock_runnable.run.assert_called_once()
        call_kwargs = mock_runnable.run.call_args[1]
        assert call_kwargs["query"] == "Analyze: test input"
        assert result == mock_response

    def test_run_with_kwargs(self):
        """Test run method passes kwargs to underlying runnable."""
        mock_response = MockResponse(result="processed")
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.id = "test-agent"
        mock_runnable.run = Mock(return_value=mock_response)

        task = SimpleTaskRunnable(
            runnable=mock_runnable,
            query_template="Process: {query}",
            response_model=MockResponse,
            tool_ids=["tool1", "tool2"],
        )

        result = task.run(query="test")
        assert result

        call_kwargs = mock_runnable.run.call_args[1]
        assert call_kwargs["response_model"] == MockResponse
        assert call_kwargs["tool_ids"] == ["tool1", "tool2"]

    def test_run_kwargs_override(self):
        """Test that run kwargs override task kwargs."""
        mock_response = MockResponse(result="processed")
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.run = Mock(return_value=mock_response)

        task = SimpleTaskRunnable(
            runnable=mock_runnable,
            query_template="Process: {query}",
            custom_param="default",
        )

        # Call with override
        task.run(query="test", custom_param="override")

        call_kwargs = mock_runnable.run.call_args[1]
        # setdefault means task kwargs don't override call kwargs
        assert call_kwargs["custom_param"] == "override"

    @pytest.mark.asyncio
    async def test_run_async_with_query_template(self):
        """Test run_async method applies query template."""
        mock_response = MockResponse(result="processed")
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.id = "test-agent"
        mock_runnable.run_async = AsyncMock(return_value=mock_response)

        task = SimpleTaskRunnable(
            runnable=mock_runnable,
            query_template="Analyze: {query}",
        )

        result = await task.run_async(query="test input")

        mock_runnable.run_async.assert_called_once()
        call_kwargs = mock_runnable.run_async.call_args[1]
        assert call_kwargs["query"] == "Analyze: test input"
        assert result == mock_response

    @pytest.mark.asyncio
    async def test_run_async_with_kwargs(self):
        """Test run_async method passes kwargs to underlying runnable."""
        mock_response = MockResponse(result="processed")
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.run_async = AsyncMock(return_value=mock_response)

        task = SimpleTaskRunnable(
            runnable=mock_runnable,
            query_template="Process: {query}",
            response_model=MockResponse,
        )

        result = await task.run_async(query="test")
        assert result

        call_kwargs = mock_runnable.run_async.call_args[1]
        assert call_kwargs["response_model"] == MockResponse

    @pytest.mark.asyncio
    async def test_run_async_empty_query(self):
        """Test run_async with empty query."""
        mock_response = MockResponse(result="processed")
        mock_runnable = Mock(spec=AgentRunnable)
        mock_runnable.run_async = AsyncMock(return_value=mock_response)

        task = SimpleTaskRunnable(
            runnable=mock_runnable,
            query_template="Default: {query}",
        )

        result = await task.run_async(query="")
        assert result

        call_kwargs = mock_runnable.run_async.call_args[1]
        assert call_kwargs["query"] == "Default: "
