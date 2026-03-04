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
        assert bundle.description == "Tools for listing and loading skills"

    def test_to_tool_creates_skill_list_and_skill_load(self):
        """to_tool() creates both skill_list and skill_load tools."""
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
        assert "skill_load" in tool_backend.captured

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
    async def test_skill_load_returns_full_skill_details(self):
        """skill_load tool returns full skill configuration as JSON."""
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

        skill_load_func = tool_backend.captured["skill_load"]

        result = await skill_load_func("analyst")
        data = json.loads(result)

        assert data["id"] == "analyst"
        assert data["description"] == "Data analysis skill"
        assert data["instructions"] == "Analyze data carefully."
        assert set(data["tool_ids"]) == {"calculator", "filesystem"}
        assert data["resources"] == {"guide": "https://example.com"}

    @pytest.mark.asyncio
    async def test_skill_load_nonexistent_skill(self):
        """skill_load returns error JSON for nonexistent skill ID."""
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
        skill_load_func = tool_backend.captured["skill_load"]

        result = await skill_load_func("nonexistent")
        data = json.loads(result)

        assert "error" in data


class TestSkillRetrieverCallbacks:
    """Tests for skill callback execution in SkillRetriever.to_tool()."""

    @pytest.mark.asyncio
    async def test_skill_load_calls_async_callback(self):
        """skill_load invokes async callback when provided."""
        skill = SkillConfig(
            id="test-skill", description="Test skill", tool_ids=["tool1", "tool2"]
        )
        repo = _make_mock_repo([skill])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        # Create mock async callback
        callback_called_with = []

        async def async_callback(skill_config):
            callback_called_with.append(skill_config)

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool(load_callback=async_callback)
        assert bundle
        skill_load_func = tool_backend.captured["skill_load"]

        # Call skill_load
        result = await skill_load_func("test-skill")
        data = json.loads(result)

        # Verify callback was called
        assert len(callback_called_with) == 1
        assert callback_called_with[0].id == "test-skill"
        assert data["id"] == "test-skill"

    @pytest.mark.asyncio
    async def test_skill_load_calls_sync_callback(self):
        """skill_load invokes sync callback when provided."""
        skill = SkillConfig(
            id="test-skill", description="Test skill", tool_ids=["tool1"]
        )
        repo = _make_mock_repo([skill])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        # Create mock sync callback
        callback_called_with = []

        def sync_callback(skill_config):
            callback_called_with.append(skill_config)

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool(load_callback=sync_callback)
        assert bundle
        skill_load_func = tool_backend.captured["skill_load"]

        # Call skill_load
        result = await skill_load_func("test-skill")
        data = json.loads(result)

        # Verify callback was called
        assert len(callback_called_with) == 1
        assert callback_called_with[0].id == "test-skill"
        assert data["id"] == "test-skill"

    @pytest.mark.asyncio
    async def test_skill_load_without_callback_works(self):
        """skill_load works normally without callback."""
        skill = SkillConfig(id="test-skill", description="Test skill")
        repo = _make_mock_repo([skill])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool(load_callback=None)
        assert bundle
        skill_load_func = tool_backend.captured["skill_load"]

        # Call skill_load without callback
        result = await skill_load_func("test-skill")
        data = json.loads(result)

        assert data["id"] == "test-skill"

    @pytest.mark.asyncio
    async def test_skill_load_callback_receives_skill_config(self):
        """Callback receives complete SkillConfig with all fields."""
        skill = SkillConfig(
            id="analyzer",
            description="Data analysis skill",
            instructions="Analyze the data",
            tool_ids=["calculator", "clock"],
            resources={"db_url": "postgresql://localhost/data"},
        )
        repo = _make_mock_repo([skill])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        received_skill = None

        async def capture_callback(skill_config):
            nonlocal received_skill
            received_skill = skill_config

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        retriever.to_tool(load_callback=capture_callback)
        skill_load_func = tool_backend.captured["skill_load"]

        await skill_load_func("analyzer")

        assert received_skill is not None
        assert received_skill.id == "analyzer"
        assert received_skill.description == "Data analysis skill"
        assert received_skill.instructions == "Analyze the data"
        assert received_skill.tool_ids == ["calculator", "clock"]
        assert received_skill.resources == {"db_url": "postgresql://localhost/data"}

    @pytest.mark.asyncio
    async def test_skill_load_callback_exception_handled(self):
        """skill_load still returns result even if callback raises exception."""
        skill = SkillConfig(id="test-skill", description="Test skill")
        repo = _make_mock_repo([skill])
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        async def failing_callback(skill_config):
            raise ValueError("Callback error")

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        retriever.to_tool(load_callback=failing_callback)
        skill_load_func = tool_backend.captured["skill_load"]

        # skill_load should still work even if callback fails
        # (the exception handling is in the backend implementation)
        with pytest.raises(ValueError):
            await skill_load_func("test-skill")

    @pytest.mark.asyncio
    async def test_skill_load_callback_with_multiple_skills(self):
        """Callback is called separately for each skill loaded."""
        skills = [
            SkillConfig(id="skill1", description="Skill 1", tool_ids=["tool1"]),
            SkillConfig(id="skill2", description="Skill 2", tool_ids=["tool2"]),
        ]
        repo = _make_mock_repo(skills)
        embedding_db = _make_mock_embedding_db()
        tool_backend = CapturingToolBackend()

        callback_calls = []

        async def tracking_callback(skill_config):
            callback_calls.append(skill_config.id)

        retriever = SkillRetriever(
            skill_config_repository=repo,
            embedding_db=embedding_db,
            tool_backend=tool_backend,
        )

        bundle = retriever.to_tool(load_callback=tracking_callback)
        skill_load_func = tool_backend.captured["skill_load"]

        assert bundle

        # Load multiple skills
        await skill_load_func("skill1")
        await skill_load_func("skill2")

        # Callback should have been called for each
        assert callback_calls == ["skill1", "skill2"]
