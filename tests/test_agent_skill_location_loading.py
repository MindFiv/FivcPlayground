"""
Tests for skill location (directory/file/URL) detection and loading.

Tests verify that skill_ids are correctly classified as either:
- Skill IDs: string identifiers managed by SkillRetriever
- Skill locations: file paths, directories, or URLs to load via StrandsSkillsPlugin

This is the new feature supporting Strands' AgentSkills plugin for
loading skills from arbitrary directories and URLs.
"""

import os
import tempfile
from pathlib import Path

import pytest

from fivcplayground.skills.types import SkillConfig


class TestSkillLocationDetection:
    """Test the skill location vs. skill ID classification logic."""

    def _classify_skill_entries(self, entries: set[str]) -> tuple[list[str], list[str]]:
        """Simulate the classification logic from StrandsAgentRunnable.run_async()."""
        agent_skill_ids = []
        agent_skill_locations = []
        for s in entries:
            if os.path.isdir(s) or os.path.isfile(s) or s.startswith("https://"):
                agent_skill_locations.append(s)
            else:
                agent_skill_ids.append(s)
        return agent_skill_ids, agent_skill_locations

    def test_skill_id_simple_string(self):
        """Simple string identifiers are classified as skill IDs."""
        agent_skill_ids, agent_skill_locations = self._classify_skill_entries(
            {"analyzer", "researcher"}
        )
        assert set(agent_skill_ids) == {"analyzer", "researcher"}
        assert agent_skill_locations == []

    def test_skill_location_directory(self):
        """Directory paths are classified as skill locations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_skill_ids, agent_skill_locations = self._classify_skill_entries(
                {tmpdir}
            )
            assert agent_skill_ids == []
            assert agent_skill_locations == [tmpdir]

    def test_skill_location_file(self):
        """File paths are classified as skill locations."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            filepath = f.name
        try:
            agent_skill_ids, agent_skill_locations = self._classify_skill_entries(
                {filepath}
            )
            assert agent_skill_ids == []
            assert agent_skill_locations == [filepath]
        finally:
            os.unlink(filepath)

    def test_skill_location_url(self):
        """HTTPS URLs are classified as skill locations."""
        url = "https://example.com/skills.tar.gz"
        agent_skill_ids, agent_skill_locations = self._classify_skill_entries({url})
        assert agent_skill_ids == []
        assert agent_skill_locations == [url]

    def test_skill_location_url_other_protocols(self):
        """Non-HTTPS URLs (http, ftp) are classified as skill IDs (not recognized as locations)."""
        # Current logic only recognizes https:// URLs, so http:// and ftp:// are treated as skill IDs
        http_url = "http://example.com/skills.tar.gz"
        ftp_url = "ftp://example.com/skills.tar.gz"
        agent_skill_ids, agent_skill_locations = self._classify_skill_entries(
            {http_url, ftp_url}
        )
        # These don't match any location criteria, so they're treated as skill IDs
        assert set(agent_skill_ids) == {http_url, ftp_url}
        assert agent_skill_locations == []

    def test_mixed_skill_ids_and_locations(self):
        """Mixed collection of IDs and locations are correctly separated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            entries = {
                "analyzer",  # skill ID
                "researcher",  # skill ID
                tmpdir,  # skill location (directory)
                "https://example.com/skills.tar.gz",  # skill location (URL)
            }
            agent_skill_ids, agent_skill_locations = self._classify_skill_entries(
                entries
            )
            assert set(agent_skill_ids) == {"analyzer", "researcher"}
            assert set(agent_skill_locations) == {
                tmpdir,
                "https://example.com/skills.tar.gz",
            }

    def test_nonexistent_path_treated_as_skill_id(self):
        """Non-existent paths are treated as skill IDs (not detected as locations)."""
        nonexistent = "/this/path/does/not/exist"
        agent_skill_ids, agent_skill_locations = self._classify_skill_entries(
            {nonexistent}
        )
        # os.path.isdir() and os.path.isfile() both return False for non-existent paths
        assert agent_skill_ids == [nonexistent]
        assert agent_skill_locations == []

    def test_relative_directory_path(self):
        """Relative directory paths are detected as locations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a subdirectory
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            agent_skill_ids, agent_skill_locations = self._classify_skill_entries(
                {str(subdir)}
            )
            assert agent_skill_ids == []
            assert agent_skill_locations == [str(subdir)]

    def test_empty_collection(self):
        """Empty collection results in empty classifications."""
        agent_skill_ids, agent_skill_locations = self._classify_skill_entries(set())
        assert agent_skill_ids == []
        assert agent_skill_locations == []


class TestSkillIdAndLocationMerging:
    """Test merging of skill_ids from config and runtime, with location separation."""

    def _merge_and_classify(
        self,
        config_skill_ids: list[str] | None,
        runtime_skill_ids: list[str] | None,
    ) -> tuple[list[str], list[str]]:
        """Simulate the full merging and classification logic."""
        # Step 1: Merge config and runtime skill_ids using set union
        agent_skill_mixed_ids = set(runtime_skill_ids) if runtime_skill_ids else set()
        agent_skill_mixed_ids.update(config_skill_ids or [])

        # Step 2: Classify into skill_ids vs. skill_locations
        agent_skill_ids = []
        agent_skill_locations = []
        for s in agent_skill_mixed_ids:
            if os.path.isdir(s) or os.path.isfile(s) or s.startswith("https://"):
                agent_skill_locations.append(s)
            else:
                agent_skill_ids.append(s)

        return agent_skill_ids, agent_skill_locations

    def test_config_only_all_ids(self):
        """Config-only skill IDs are not classified as locations."""
        agent_skill_ids, agent_skill_locations = self._merge_and_classify(
            config_skill_ids=["analyzer", "researcher"],
            runtime_skill_ids=None,
        )
        assert set(agent_skill_ids) == {"analyzer", "researcher"}
        assert agent_skill_locations == []

    def test_runtime_only_all_ids(self):
        """Runtime-only skill IDs are not classified as locations."""
        agent_skill_ids, agent_skill_locations = self._merge_and_classify(
            config_skill_ids=None,
            runtime_skill_ids=["analyzer", "researcher"],
        )
        assert set(agent_skill_ids) == {"analyzer", "researcher"}
        assert agent_skill_locations == []

    def test_config_and_runtime_merged_with_ids(self):
        """Config and runtime IDs are merged via set union."""
        agent_skill_ids, agent_skill_locations = self._merge_and_classify(
            config_skill_ids=["analyzer", "researcher"],
            runtime_skill_ids=["researcher", "planner"],
        )
        # Union: analyzer, researcher, planner (deduped)
        assert set(agent_skill_ids) == {"analyzer", "researcher", "planner"}
        assert agent_skill_locations == []

    def test_config_location_runtime_id(self):
        """Config with directory location, runtime with skill ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_skill_ids, agent_skill_locations = self._merge_and_classify(
                config_skill_ids=[tmpdir],
                runtime_skill_ids=["analyzer"],
            )
            assert agent_skill_ids == ["analyzer"]
            assert agent_skill_locations == [tmpdir]

    def test_config_id_runtime_location(self):
        """Config with skill ID, runtime with directory location."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_skill_ids, agent_skill_locations = self._merge_and_classify(
                config_skill_ids=["analyzer"],
                runtime_skill_ids=[tmpdir],
            )
            assert agent_skill_ids == ["analyzer"]
            assert agent_skill_locations == [tmpdir]

    def test_config_and_runtime_both_mixed(self):
        """Both config and runtime have mix of IDs and locations."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                agent_skill_ids, agent_skill_locations = self._merge_and_classify(
                    config_skill_ids=["analyzer", tmpdir1],
                    runtime_skill_ids=["researcher", tmpdir2],
                )
                assert set(agent_skill_ids) == {"analyzer", "researcher"}
                assert set(agent_skill_locations) == {tmpdir1, tmpdir2}

    def test_overlapping_entries_deduplicated(self):
        """Overlapping entries between config and runtime are deduplicated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_skill_ids, agent_skill_locations = self._merge_and_classify(
                config_skill_ids=["analyzer", tmpdir],
                runtime_skill_ids=["analyzer", tmpdir],
            )
            # Set union removes duplicates
            assert agent_skill_ids == ["analyzer"]
            assert agent_skill_locations == [tmpdir]

    def test_both_none_results_in_empty(self):
        """Both None results in empty lists."""
        agent_skill_ids, agent_skill_locations = self._merge_and_classify(
            config_skill_ids=None,
            runtime_skill_ids=None,
        )
        assert agent_skill_ids == []
        assert agent_skill_locations == []

    def test_both_empty_lists_results_in_empty(self):
        """Both empty lists result in empty lists."""
        agent_skill_ids, agent_skill_locations = self._merge_and_classify(
            config_skill_ids=[],
            runtime_skill_ids=[],
        )
        assert agent_skill_ids == []
        assert agent_skill_locations == []


class TestStrandsSkillsPluginCreation:
    """Test the logic for creating StrandsSkillsPlugin with classified locations."""

    def _should_create_plugin(self, agent_skill_locations: list[str]) -> bool:
        """Determine if plugin should be created based on locations."""
        return bool(agent_skill_locations)

    def test_plugin_created_when_locations_exist(self):
        """Plugin is created when there are skill locations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            should_create = self._should_create_plugin([tmpdir])
            assert should_create is True

    def test_plugin_not_created_when_no_locations(self):
        """Plugin is not created when there are no skill locations."""
        should_create = self._should_create_plugin([])
        assert should_create is False

    def test_plugin_created_with_multiple_locations(self):
        """Plugin is created when multiple locations are present."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                should_create = self._should_create_plugin([tmpdir1, tmpdir2])
                assert should_create is True

    def test_plugin_created_with_url_location(self):
        """Plugin is created when URL location is present."""
        should_create = self._should_create_plugin(
            ["https://example.com/skills.tar.gz"]
        )
        assert should_create is True

    def test_plugin_passed_to_agent_constructor(self):
        """Simulates plugin parameter passed to agent constructor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_skill_locations = [tmpdir]
            # Simulate the Strands agent constructor call
            agent_skill_plugin = (
                {"skills": agent_skill_locations}  # Simulating StrandsSkillsPlugin
                if agent_skill_locations
                else None
            )
            assert agent_skill_plugin is not None
            assert agent_skill_plugin["skills"] == [tmpdir]

    def test_none_plugin_when_no_locations(self):
        """Plugin parameter is None when no locations exist."""
        agent_skill_locations = []
        # Simulate the conditional in run_async
        agent_skill_plugin = (
            {"skills": agent_skill_locations} if agent_skill_locations else None
        )
        assert agent_skill_plugin is None


class TestBackwardCompatibilityWithSkillIds:
    """Test that existing skill ID system still works with new location detection."""

    def test_pure_skill_ids_unchanged(self):
        """Pure skill IDs continue to work as before."""
        agent_skill_ids, agent_skill_locations = self._classify(
            {"analyzer", "researcher", "planner"}
        )
        assert set(agent_skill_ids) == {"analyzer", "researcher", "planner"}
        assert agent_skill_locations == []

    def test_skill_retriever_can_process_ids(self):
        """Skill IDs (non-locations) can be passed to skill_retriever."""
        agent_skill_ids = ["analyzer", "researcher"]
        # These are passed to skill_retriever.to_tool(skill_ids=agent_skill_ids)
        # Skill retriever looks them up in embedding DB
        assert all(
            isinstance(sid, str) and not ("/" in sid or sid.startswith("https://"))
            for sid in agent_skill_ids
        )

    def test_only_ids_no_locations_no_plugin(self):
        """When only skill IDs exist (no locations), plugin is not created."""
        agent_skill_ids, agent_skill_locations = self._classify(
            {"analyzer", "researcher"}
        )
        agent_skill_plugin = (
            {"skills": agent_skill_locations} if agent_skill_locations else None
        )
        assert agent_skill_plugin is None
        assert set(agent_skill_ids) == {"analyzer", "researcher"}

    def _classify(self, entries):
        """Helper to classify entries."""
        agent_skill_ids = []
        agent_skill_locations = []
        for s in entries:
            if os.path.isdir(s) or os.path.isfile(s) or s.startswith("https://"):
                agent_skill_locations.append(s)
            else:
                agent_skill_ids.append(s)
        return agent_skill_ids, agent_skill_locations


class _StubSkillRetriever:
    """Minimal stand-in for SkillRetriever that maps id -> SkillConfig."""

    def __init__(self, skills: dict[str, SkillConfig]):
        self._skills = skills

    async def get_skill_async(self, skill_id: str) -> SkillConfig | None:
        return self._skills.get(skill_id)


async def _resolve_path_bearing_skills(
    agent_skill_ids: list[str],
    agent_skill_locations: list[str],
    skill_retriever: _StubSkillRetriever | None,
) -> tuple[list[str], list[str]]:
    """Mirror StrandsAgentRunnable.run_async() path-resolution branch.

    Resolves any registered skill IDs whose SkillConfig has a `path` and
    appends those paths to agent_skill_locations. agent_skill_ids is left
    intact so the SkillRetriever still surfaces them via `skill_list()`.
    """
    if skill_retriever and agent_skill_ids:
        for sid in agent_skill_ids:
            skill = await skill_retriever.get_skill_async(sid)
            if skill and skill.path:
                agent_skill_locations.append(skill.path)
    return agent_skill_ids, agent_skill_locations


class TestSkillConfigPathRouting:
    """Test that SkillConfig.path is routed into StrandsSkillsPlugin at run time."""

    @staticmethod
    def _classify(entries: set[str]) -> tuple[list[str], list[str]]:
        agent_skill_ids: list[str] = []
        agent_skill_locations: list[str] = []
        for s in entries:
            if os.path.isdir(s) or os.path.isfile(s) or s.startswith("https://"):
                agent_skill_locations.append(s)
            else:
                agent_skill_ids.append(s)
        return agent_skill_ids, agent_skill_locations

    @pytest.mark.asyncio
    async def test_path_bearing_skill_routed_to_plugin(self):
        """A SkillConfig with `path` set adds the path to skill_locations."""
        retriever = _StubSkillRetriever(
            {
                "external": SkillConfig(
                    id="external",
                    description="External skill",
                    path="https://example.com/skills/external.tar.gz",
                ),
            }
        )
        ids, locations = self._classify({"external"})
        ids, locations = await _resolve_path_bearing_skills(ids, locations, retriever)

        assert locations == ["https://example.com/skills/external.tar.gz"]
        # ID stays in the retriever-facing list so skill_list() still surfaces it.
        assert ids == ["external"]

    @pytest.mark.asyncio
    async def test_inline_skill_unchanged(self):
        """A SkillConfig without `path` does not contribute to skill_locations."""
        retriever = _StubSkillRetriever(
            {
                "inline": SkillConfig(
                    id="inline",
                    description="Inline skill",
                    instructions="Do stuff",
                    tool_ids=["calculator"],
                ),
            }
        )
        ids, locations = self._classify({"inline"})
        ids, locations = await _resolve_path_bearing_skills(ids, locations, retriever)

        assert locations == []
        assert ids == ["inline"]

    @pytest.mark.asyncio
    async def test_mixed_path_inline_and_raw_location(self):
        """Path-bearing ID + inline ID + raw location all land correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            retriever = _StubSkillRetriever(
                {
                    "with-path": SkillConfig(
                        id="with-path",
                        description="Path-bearing skill",
                        path="/skills/with-path",
                    ),
                    "inline": SkillConfig(
                        id="inline",
                        description="Inline skill",
                        tool_ids=["clock"],
                    ),
                }
            )
            ids, locations = self._classify({"with-path", "inline", tmpdir})
            ids, locations = await _resolve_path_bearing_skills(
                ids, locations, retriever
            )

            assert set(ids) == {"with-path", "inline"}
            assert set(locations) == {tmpdir, "/skills/with-path"}

    @pytest.mark.asyncio
    async def test_no_retriever_no_resolution(self):
        """Without a retriever, path-resolution is skipped (backward compatible)."""
        ids, locations = self._classify({"external", "inline"})
        ids, locations = await _resolve_path_bearing_skills(ids, locations, None)

        assert set(ids) == {"external", "inline"}
        assert locations == []

    @pytest.mark.asyncio
    async def test_unknown_skill_id_no_resolution(self):
        """Skill IDs absent from the retriever are left in agent_skill_ids."""
        retriever = _StubSkillRetriever({})  # empty
        ids, locations = self._classify({"missing"})
        ids, locations = await _resolve_path_bearing_skills(ids, locations, retriever)

        assert ids == ["missing"]
        assert locations == []
