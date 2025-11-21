"""Tests for FileAgentConfigRepository class."""

import json
import tempfile

from fivcplayground.agents.types.base import AgentConfig
from fivcplayground.agents.types.repositories.files import FileAgentConfigRepository
from fivcplayground.utils import OutputDir


class TestFileAgentConfigRepository:
    """Tests for FileAgentConfigRepository class"""

    def test_initialization_with_output_dir(self):
        """Test repository initialization with custom output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    def test_initialization_without_output_dir(self):
        """Test repository initialization with default output directory"""
        repo = FileAgentConfigRepository()
        assert repo.base_path.exists()
        assert repo.base_path.is_dir()

    def test_update_and_get_agent_config(self):
        """Test creating and retrieving an agent configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create agent config
            agent_config = AgentConfig(
                id="test-agent",
                description="Test agent description",
                system_prompt="You are a helpful assistant",
            )

            # Save agent config
            repo.update_agent_config(agent_config)

            # Verify file exists
            config_file = repo._get_agent_config_file("test-agent")
            assert config_file.exists()

            # Retrieve agent config
            retrieved_config = repo.get_agent_config("test-agent")
            assert retrieved_config is not None
            assert retrieved_config.id == "test-agent"
            assert retrieved_config.description == "Test agent description"
            assert retrieved_config.system_prompt == "You are a helpful assistant"

    def test_get_nonexistent_agent_config(self):
        """Test retrieving a non-existent agent configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Try to get non-existent config
            config = repo.get_agent_config("nonexistent-agent")
            assert config is None

    def test_list_agent_configs(self):
        """Test listing all agent configurations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create multiple agent configs
            configs = [
                AgentConfig(id="agent1", description="Agent 1"),
                AgentConfig(id="agent2", description="Agent 2"),
                AgentConfig(id="agent3", description="Agent 3"),
            ]

            for config in configs:
                repo.update_agent_config(config)

            # List all configs
            listed_configs = repo.list_agent_configs()
            assert len(listed_configs) == 3
            config_ids = {config.id for config in listed_configs}
            assert config_ids == {"agent1", "agent2", "agent3"}

    def test_delete_agent_config(self):
        """Test deleting an agent configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create and save config
            agent_config = AgentConfig(id="test-agent", description="Test")
            repo.update_agent_config(agent_config)

            # Verify it exists
            assert repo.get_agent_config("test-agent") is not None

            # Delete config
            repo.delete_agent_config("test-agent")

            # Verify it's deleted
            assert repo.get_agent_config("test-agent") is None
            assert not repo._get_agent_config_file("test-agent").exists()

    def test_delete_nonexistent_agent_config(self):
        """Test deleting a non-existent agent configuration (should be safe)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Delete non-existent config (should not raise error)
            repo.delete_agent_config("nonexistent-agent")

    def test_filter_repository(self):
        """Test filter_repository returns self"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Filter repository
            filtered_repo = repo.filter_repository(some_filter="value")
            assert filtered_repo is repo

    def test_json_file_format(self):
        """Test that agent configs are stored in correct JSON format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create and save agent config
            agent_config = AgentConfig(
                id="test-agent",
                description="Test description",
                system_prompt="Test prompt",
            )
            repo.update_agent_config(agent_config)

            # Read JSON file directly
            config_file = repo._get_agent_config_file("test-agent")
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Verify JSON structure
            assert data["id"] == "test-agent"
            assert data["description"] == "Test description"
            assert data["system_prompt"] == "Test prompt"

    def test_file_naming_pattern(self):
        """Test that agent configs use the correct file naming pattern"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create and save agent config
            agent_config = AgentConfig(id="my-agent", description="Test")
            repo.update_agent_config(agent_config)

            # Verify file naming pattern is agent_<agent_id>.json
            config_file = repo._get_agent_config_file("my-agent")
            assert config_file.name == "agent_my-agent.json"
            assert config_file.exists()

            # Verify glob pattern matches the file
            glob_results = list(repo.base_path.glob("agent_*.json"))
            assert len(glob_results) == 1
            assert glob_results[0].name == "agent_my-agent.json"
