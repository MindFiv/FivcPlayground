#!/usr/bin/env python3
"""Tests for create_skill_tools_async (SkillToolset)."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fivcplayground.skills import create_skill_tools_async
from fivcplayground.skills.types.base import SkillConfig
from fivcplayground.tools.types.bundles import FunctionToolBundle


class CapturingToolBackend:
    """Mock ToolBackend that captures functions passed to create_tool."""

    def __init__(self):
        self.captured: dict[str, object] = {}

    def create_tool(self, func, tool_name=None, tool_description=None):
        name = tool_name or func.__name__
        self.captured[name] = func
        return MagicMock()

    def create_tool_bundle(self, config):
        return MagicMock()


def _make_skill_retriever(
    skills_by_id: dict[str, SkillConfig], retrieved: list[SkillConfig] | None = None
):
    """Create a mock SkillRetriever."""
    retriever = MagicMock()
    retriever.get_skill_async = AsyncMock(side_effect=lambda sid: skills_by_id.get(sid))
    retriever.retrieve_skills_async = AsyncMock(return_value=retrieved or [])
    return retriever


class TestCreateSkillToolsAsync:
    """Tests for create_skill_tools_async factory."""

    @pytest.mark.asyncio
    async def test_returns_function_tool_bundle(self):
        """create_skill_tools_async returns a FunctionToolBundle named 'skills'."""
        retriever = _make_skill_retriever({})
        tool_backend = CapturingToolBackend()

        bundle = await create_skill_tools_async(retriever, tool_backend)

        assert isinstance(bundle, FunctionToolBundle)
        assert bundle.name == "skills"

    @pytest.mark.asyncio
    async def test_skill_find_returns_matching_skills(self):
        """skill_find returns JSON list of matching skill id and description."""
        skill = SkillConfig(
            id="analyst",
            description="Data analysis skill",
            instructions="Analyze carefully.",
            tool_ids=["calculator"],
        )
        retriever = _make_skill_retriever({}, retrieved=[skill])
        tool_backend = CapturingToolBackend()

        await create_skill_tools_async(retriever, tool_backend)

        skill_find = tool_backend.captured["skill_find"]
        result = await skill_find("data analysis")
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "analyst"
        assert data[0]["description"] == "Data analysis skill"
        retriever.retrieve_skills_async.assert_called_once_with("data analysis")

    @pytest.mark.asyncio
    async def test_skill_find_no_results(self):
        """skill_find returns empty JSON list when retriever finds nothing."""
        retriever = _make_skill_retriever({}, retrieved=[])
        tool_backend = CapturingToolBackend()

        await create_skill_tools_async(retriever, tool_backend)

        skill_find = tool_backend.captured["skill_find"]
        result = await skill_find("unknown task")
        data = json.loads(result)

        assert data == []

    @pytest.mark.asyncio
    async def test_skill_execute_returns_instructions(self):
        """skill_execute returns JSON with instructions, suggested_tool_ids, resources."""
        skill = SkillConfig(
            id="researcher",
            description="Research skill",
            instructions="Research thoroughly.",
            tool_ids=["filesystem", "clock"],
            resources={"guide": "See https://example.com"},
        )
        retriever = _make_skill_retriever({"researcher": skill})
        tool_backend = CapturingToolBackend()

        await create_skill_tools_async(retriever, tool_backend)

        skill_execute = tool_backend.captured["skill_execute"]
        result = await skill_execute("researcher")
        data = json.loads(result)

        assert data["id"] == "researcher"
        assert data["instructions"] == "Research thoroughly."
        assert set(data["suggested_tool_ids"]) == {"filesystem", "clock"}
        assert data["resources"] == {"guide": "See https://example.com"}

    @pytest.mark.asyncio
    async def test_skill_execute_missing_optional_fields(self):
        """skill_execute omits instructions/suggested_tool_ids/resources when absent."""
        skill = SkillConfig(
            id="minimal",
            description="Minimal skill",
        )
        retriever = _make_skill_retriever({"minimal": skill})
        tool_backend = CapturingToolBackend()

        await create_skill_tools_async(retriever, tool_backend)

        skill_execute = tool_backend.captured["skill_execute"]
        result = await skill_execute("minimal")
        data = json.loads(result)

        assert data == {"id": "minimal"}
        assert "instructions" not in data
        assert "suggested_tool_ids" not in data
        assert "resources" not in data

    @pytest.mark.asyncio
    async def test_skill_execute_unknown_id(self):
        """skill_execute returns error JSON for unknown skill ID."""
        retriever = _make_skill_retriever({})
        tool_backend = CapturingToolBackend()

        await create_skill_tools_async(retriever, tool_backend)

        skill_execute = tool_backend.captured["skill_execute"]
        result = await skill_execute("nonexistent")
        data = json.loads(result)

        assert "error" in data
        assert "nonexistent" in data["error"]
