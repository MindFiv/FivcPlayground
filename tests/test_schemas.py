#!/usr/bin/env python3
"""
Tests for task schemas.

Note: All task schemas have been moved to fivcadvisor.tasks.types.base
Tests remain here but import from new location.
"""

import pytest
from pydantic import ValidationError

from fivcplayground.tasks.types import (
    TaskAssessment,
)


class TestTaskAssessment:
    """Test the TaskAssessment schema."""

    def test_init_basic(self):
        """Test basic TaskAssessment initialization."""
        assessment = TaskAssessment(
            require_planning=True,
            reasoning="This is a complex task",
        )

        assert assessment.require_planning is True
        assert assessment.reasoning == "This is a complex task"

    def test_init_no_tools(self):
        """Test TaskAssessment with no planning required."""
        assessment = TaskAssessment(
            require_planning=False,
            reasoning="Simple task",
        )

        assert assessment.require_planning is False
        assert assessment.reasoning == "Simple task"

    def test_validation_error(self):
        """Test that missing required fields raises ValidationError."""
        with pytest.raises(ValidationError):
            TaskAssessment()

    def test_dict_conversion(self):
        """Test conversion to dictionary."""
        assessment = TaskAssessment(
            require_planning=True,
            reasoning="test reasoning",
        )
        data = assessment.model_dump()

        assert data["require_planning"] is True
        assert data["reasoning"] == "test reasoning"

    def test_json_schema(self):
        """Test JSON schema generation."""
        schema = TaskAssessment.model_json_schema()

        assert "properties" in schema
        # Check for alias names in schema (Pydantic uses aliases in JSON schema)
        assert "requires_planning_agent" in schema["properties"]
        assert "reasoning" in schema["properties"]


if __name__ == "__main__":
    pytest.main([__file__])
