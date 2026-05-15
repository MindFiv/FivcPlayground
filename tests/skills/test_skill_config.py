#!/usr/bin/env python3
"""Tests for SkillConfig model."""

import pytest
from fivcplayground.skills.types.base import SkillConfig


class TestSkillConfig:
    """Tests for SkillConfig Pydantic model."""

    def test_minimal_config(self):
        """Test creating a SkillConfig with only required fields."""
        config = SkillConfig(
            id="test-skill",
            description="A test skill for testing",
        )
        assert config.id == "test-skill"
        assert config.description == "A test skill for testing"
        assert config.path is None
        assert config.instructions is None
        assert config.tool_ids is None
        assert config.resources is None

    def test_full_config(self):
        """Test creating a SkillConfig with all fields."""
        config = SkillConfig(
            id="data-analyst",
            description="Skill for analyzing data",
            path="/skills/data-analyst",
            instructions="You excel at analyzing structured data.",
            tool_ids=["calculator", "filesystem"],
            resources={"formulas": "# Common Formulas\n- Mean: sum/count"},
        )
        assert config.id == "data-analyst"
        assert config.description == "Skill for analyzing data"
        assert config.path == "/skills/data-analyst"
        assert config.instructions == "You excel at analyzing structured data."
        assert config.tool_ids == ["calculator", "filesystem"]
        assert config.resources == {"formulas": "# Common Formulas\n- Mean: sum/count"}

    def test_path_only_config(self):
        """Test a SkillConfig that delegates to an external path/URL."""
        config = SkillConfig(
            id="external-skill",
            description="Skill loaded from a directory",
            path="https://example.com/skills/external.tar.gz",
        )
        assert config.path == "https://example.com/skills/external.tar.gz"
        assert config.instructions is None
        assert config.tool_ids is None
        assert config.resources is None

    def test_serialization(self):
        """Test SkillConfig serialization to dict."""
        config = SkillConfig(
            id="web-researcher",
            description="Skill for web research",
            path="/skills/web-researcher",
            instructions="Search multiple sources.",
            tool_ids=["playwright"],
        )
        data = config.model_dump(mode="json")
        assert data["id"] == "web-researcher"
        assert data["description"] == "Skill for web research"
        assert data["path"] == "/skills/web-researcher"
        assert data["tool_ids"] == ["playwright"]
        assert data["instructions"] == "Search multiple sources."
        assert data["resources"] is None

    def test_deserialization(self):
        """Test SkillConfig deserialization from dict."""
        data = {
            "id": "researcher",
            "description": "Research skill",
            "path": "/skills/researcher",
            "instructions": "Be thorough.",
            "tool_ids": ["search", "filesystem"],
            "resources": {"ref": "Reference material"},
        }
        config = SkillConfig.model_validate(data)
        assert config.id == "researcher"
        assert config.description == "Research skill"
        assert config.path == "/skills/researcher"
        assert config.tool_ids == ["search", "filesystem"]
        assert config.resources == {"ref": "Reference material"}

    def test_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        with pytest.raises(Exception):
            SkillConfig(id="test")  # missing description
