#!/usr/bin/env python3
"""Tests for FileSkillConfigRepository."""

import pytest
import yaml
import tempfile

from fivcplayground.skills.types.base import SkillConfig
from fivcplayground.skills.types.repositories.files import FileSkillConfigRepository
from fivcplayground.utils import OutputDir


class TestFileSkillConfigRepository:
    """Tests for FileSkillConfigRepository."""

    @pytest.mark.asyncio
    async def test_initialization_with_output_dir(self):
        """Test repository initialization with custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileSkillConfigRepository(output_dir=output_dir)
            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    @pytest.mark.asyncio
    async def test_empty_repository_returns_empty_list(self):
        """Test that listing an empty repository returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))
            configs = await repo.list_skill_configs_async()
            assert configs == []

    @pytest.mark.asyncio
    async def test_get_nonexistent_skill(self):
        """Test that getting a nonexistent skill returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))
            result = await repo.get_skill_config_async("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_update_and_get_skill_config(self):
        """Test creating and retrieving a skill configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))

            skill = SkillConfig(
                id="data-analyst",
                description="Skill for analyzing data",
                instructions="You excel at analyzing structured data.",
                tool_ids=["calculator", "filesystem"],
            )
            await repo.update_skill_config_async(skill)

            retrieved = await repo.get_skill_config_async("data-analyst")
            assert retrieved is not None
            assert retrieved.id == "data-analyst"
            assert retrieved.description == "Skill for analyzing data"
            assert retrieved.instructions == "You excel at analyzing structured data."
            assert retrieved.tool_ids == ["calculator", "filesystem"]

    @pytest.mark.asyncio
    async def test_update_existing_skill_config(self):
        """Test updating an existing skill configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))

            original = SkillConfig(
                id="researcher",
                description="Research skill",
                instructions="Search carefully.",
            )
            await repo.update_skill_config_async(original)

            updated = SkillConfig(
                id="researcher",
                description="Enhanced research skill",
                instructions="Search very carefully.",
                tool_ids=["search"],
            )
            await repo.update_skill_config_async(updated)

            retrieved = await repo.get_skill_config_async("researcher")
            assert retrieved.description == "Enhanced research skill"
            assert retrieved.instructions == "Search very carefully."
            assert retrieved.tool_ids == ["search"]

    @pytest.mark.asyncio
    async def test_list_skill_configs(self):
        """Test listing all skill configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))

            skills = [
                SkillConfig(id="skill-a", description="Desc A"),
                SkillConfig(id="skill-b", description="Desc B"),
                SkillConfig(id="skill-c", description="Desc C"),
            ]
            for skill in skills:
                await repo.update_skill_config_async(skill)

            listed = await repo.list_skill_configs_async()
            assert len(listed) == 3
            ids = {s.id for s in listed}
            assert ids == {"skill-a", "skill-b", "skill-c"}

    @pytest.mark.asyncio
    async def test_delete_skill_config(self):
        """Test deleting a skill configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))

            skill = SkillConfig(id="temp-skill", description="Temp skill")
            await repo.update_skill_config_async(skill)

            assert await repo.get_skill_config_async("temp-skill") is not None

            await repo.delete_skill_config_async("temp-skill")

            assert await repo.get_skill_config_async("temp-skill") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_skill(self):
        """Test that deleting a nonexistent skill is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))
            await repo.delete_skill_config_async("nonexistent")  # should not raise

    @pytest.mark.asyncio
    async def test_yaml_file_format(self):
        """Test that skills are stored in correct YAML format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))

            skill = SkillConfig(
                id="test-skill",
                description="A test",
                instructions="Do the test.",
                tool_ids=["tool1", "tool2"],
            )
            await repo.update_skill_config_async(skill)

            with open(repo.skills_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            assert "test-skill" in data
            assert data["test-skill"]["description"] == "A test"
            assert data["test-skill"]["tool_ids"] == ["tool1", "tool2"]

    @pytest.mark.asyncio
    async def test_corrupted_yaml_returns_empty(self):
        """Test that corrupted YAML file is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))

            with open(repo.skills_file, "w", encoding="utf-8") as f:
                f.write("{ invalid: yaml: content: }")

            data = repo._load_skills_data()
            assert data == {}

    @pytest.mark.asyncio
    async def test_skill_with_resources(self):
        """Test storing and retrieving a skill with resources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))

            skill = SkillConfig(
                id="analyst",
                description="Data analyst",
                resources={"formulas": "# Formulas\n- Mean: sum/count"},
            )
            await repo.update_skill_config_async(skill)

            retrieved = await repo.get_skill_config_async("analyst")
            assert retrieved.resources == {"formulas": "# Formulas\n- Mean: sum/count"}
