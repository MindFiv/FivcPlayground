#!/usr/bin/env python3
"""Tests for SkillRetriever."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fivcplayground.skills.types.base import SkillConfig
from fivcplayground.skills.types.retrievers import SkillRetriever
from fivcplayground.tools.types.bundles import FunctionToolBundle


def _make_mock_embedding_db():
    """Create a mock EmbeddingDB with a skills table."""
    skill_table = MagicMock()
    skill_table.search.return_value = []
    skill_table.cleanup = MagicMock()
    skill_table.add = MagicMock()

    embedding_db = MagicMock()
    embedding_db.skills = skill_table
    return embedding_db


def _make_mock_repo(skills: list[SkillConfig]):
    """Create a mock SkillConfigRepository."""
    repo = MagicMock()
    repo.list_skill_configs_async = AsyncMock(return_value=skills)
    repo.get_skill_config_async = AsyncMock(
        side_effect=lambda sid: next((s for s in skills if s.id == sid), None)
    )
    return repo


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


class TestSkillRetriever:
    """Tests for SkillRetriever."""

    def test_initialization(self):
        """Test SkillRetriever initialization."""
        repo = _make_mock_repo([])
        embedding_db = _make_mock_embedding_db()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
        )
        assert retriever.max_num == 3
        assert retriever.min_sim == 0.3

    @pytest.mark.asyncio
    async def test_get_skill_async(self):
        """Test getting a skill by ID."""
        skill = SkillConfig(id="data-analyst", description="Analyzes data")
        repo = _make_mock_repo([skill])
        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=_make_mock_embedding_db(),
        )

        result = await retriever.get_skill_async("data-analyst")
        assert result is not None
        assert result.id == "data-analyst"

    @pytest.mark.asyncio
    async def test_get_nonexistent_skill(self):
        """Test getting a nonexistent skill returns None."""
        repo = _make_mock_repo([])
        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=_make_mock_embedding_db(),
        )

        result = await retriever.get_skill_async("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_skills_async(self):
        """Test listing all skills."""
        skills = [
            SkillConfig(id="skill-a", description="Skill A"),
            SkillConfig(id="skill-b", description="Skill B"),
        ]
        repo = _make_mock_repo(skills)
        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=_make_mock_embedding_db(),
        )

        result = await retriever.list_skills_async()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_index_skills_async(self):
        """Test indexing skills in the embedding database."""
        skills = [
            SkillConfig(id="analyst", description="Data analysis"),
            SkillConfig(id="researcher", description="Web research"),
        ]
        repo = _make_mock_repo(skills)
        embedding_db = _make_mock_embedding_db()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
        )
        await retriever.index_skills_async()

        embedding_db.skills.cleanup.assert_called_once()
        assert embedding_db.skills.add.call_count == 2

        calls = embedding_db.skills.add.call_args_list
        added_metadata = [c[1]["metadata"]["__skill__"] for c in calls]
        assert "analyst" in added_metadata
        assert "researcher" in added_metadata

    @pytest.mark.asyncio
    async def test_retrieve_skills_async_with_results(self):
        """Test semantic retrieval returns matched skills."""
        skill = SkillConfig(id="analyst", description="Data analysis")
        repo = _make_mock_repo([skill])
        embedding_db = _make_mock_embedding_db()
        # score=0.4 → sim=(2-0.4)/2=0.8 >= 0.3
        embedding_db.skills.search.return_value = [
            {"metadata": {"__skill__": "analyst"}, "score": 0.4}
        ]

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
        )

        results = await retriever.retrieve_skills_async("analyze some data")
        assert len(results) == 1
        assert results[0].id == "analyst"

    @pytest.mark.asyncio
    async def test_retrieve_skills_async_below_threshold(self):
        """Test that skills below similarity threshold are not returned."""
        skill = SkillConfig(id="analyst", description="Data analysis")
        repo = _make_mock_repo([skill])
        embedding_db = _make_mock_embedding_db()
        # score=1.5 → sim=(2-1.5)/2=0.25 < 0.3 (below threshold)
        embedding_db.skills.search.return_value = [
            {"metadata": {"__skill__": "analyst"}, "score": 1.5}
        ]

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
        )

        results = await retriever.retrieve_skills_async("unrelated query")
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_retrieve_skills_async_no_results(self):
        """Test retrieval with no embedding matches returns empty list."""
        repo = _make_mock_repo([])
        embedding_db = _make_mock_embedding_db()
        embedding_db.skills.search.return_value = []

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
        )

        results = await retriever.retrieve_skills_async("anything")
        assert results == []


class TestSkillRetrieverToTool:
    """Tests for SkillRetriever.to_tool() method."""

    def test_to_tool_returns_function_tool_bundle(self):
        """to_tool() returns a FunctionToolBundle named 'skills'."""
        repo = _make_mock_repo([])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool()

        assert isinstance(bundle, FunctionToolBundle)
        assert bundle.name == "skills"
        assert bundle.description == "Tools for listing and retrieving skills"

    def test_to_tool_creates_skill_list_and_skill_get(self):
        """to_tool() creates both skill_list and skill_get tools."""
        repo = _make_mock_repo([])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool()
        assert bundle

        # FunctionToolBundle should have created tools from the functions
        assert "skill_list" in tool_backend.captured
        assert "skill_get" in tool_backend.captured

    @pytest.mark.asyncio
    async def test_skill_list_returns_all_skills(self):
        """skill_list tool returns JSON list of all skills with id and description."""
        skills = [
            SkillConfig(id="analyst", description="Data analysis skill"),
            SkillConfig(id="researcher", description="Research skill"),
        ]
        repo = _make_mock_repo(skills)
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool()
        assert bundle

        skill_list_func = tool_backend.captured["skill_list"]

        result = await skill_list_func()
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] == "analyst"
        assert data[0]["description"] == "Data analysis skill"
        assert data[1]["id"] == "researcher"
        assert data[1]["description"] == "Research skill"

    @pytest.mark.asyncio
    async def test_skill_list_empty_repository(self):
        """skill_list returns empty JSON list when no skills exist."""
        repo = _make_mock_repo([])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool()
        assert bundle

        skill_list_func = tool_backend.captured["skill_list"]

        result = await skill_list_func()
        data = json.loads(result)

        assert data == []

    @pytest.mark.asyncio
    async def test_skill_get_returns_full_skill_details(self):
        """skill_get tool returns full skill configuration as JSON."""
        skill = SkillConfig(
            id="analyst",
            description="Data analysis skill",
            instructions="Analyze data carefully.",
            tool_ids=["calculator", "filesystem"],
            resources={"guide": "https://example.com"},
        )
        repo = _make_mock_repo([skill])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool()
        assert bundle

        skill_get_func = tool_backend.captured["skill_get"]

        result = await skill_get_func("analyst")
        data = json.loads(result)

        assert data["id"] == "analyst"
        assert data["description"] == "Data analysis skill"
        assert data["instructions"] == "Analyze data carefully."
        assert set(data["tool_ids"]) == {"calculator", "filesystem"}
        assert data["resources"] == {"guide": "https://example.com"}

    @pytest.mark.asyncio
    async def test_skill_get_nonexistent_skill(self):
        """skill_get returns error JSON for nonexistent skill ID."""
        repo = _make_mock_repo([])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool()
        assert bundle
        skill_get_func = tool_backend.captured["skill_get"]

        result = await skill_get_func("nonexistent")
        data = json.loads(result)

        assert "error" in data
        assert "nonexistent" in data["error"]
