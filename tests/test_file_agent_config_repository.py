"""Tests for FileAgentConfigRepository class."""

import yaml
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

            # Verify YAML file exists
            agents_file = repo._get_agents_file()
            assert agents_file.exists()

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

            # Verify it's deleted from YAML data
            agents_data = repo._load_agents_data()
            assert "test-agent" not in agents_data
            assert repo.get_agent_config("test-agent") is None

    def test_delete_nonexistent_agent_config(self):
        """Test deleting a non-existent agent configuration (should be safe)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Delete non-existent config (should not raise error)
            repo.delete_agent_config("nonexistent-agent")

    def test_yaml_file_format(self):
        """Test that agent configs are stored in correct YAML format"""
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

            # Read YAML file directly
            agents_file = repo._get_agents_file()
            with open(agents_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Verify YAML structure - should have agent_id as key
            assert "test-agent" in data
            agent_data = data["test-agent"]
            assert agent_data["id"] == "test-agent"
            assert agent_data["description"] == "Test description"
            assert agent_data["system_prompt"] == "Test prompt"

    def test_tool_ids_serialization(self):
        """Test that tool_ids field is properly serialized and deserialized"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create agent config with tool_ids
            agent_config = AgentConfig(
                id="test-agent-with-tools",
                description="Agent with specific tools",
                system_prompt="Test prompt",
                tool_ids=["tool1", "tool2", "tool3"],
            )
            repo.update_agent_config(agent_config)

            # Retrieve and verify tool_ids
            retrieved = repo.get_agent_config("test-agent-with-tools")
            assert retrieved is not None
            assert retrieved.tool_ids == ["tool1", "tool2", "tool3"]

            # Verify YAML file contains tool_ids
            agents_file = repo._get_agents_file()
            with open(agents_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            agent_data = data["test-agent-with-tools"]
            assert agent_data["tool_ids"] == ["tool1", "tool2", "tool3"]

    def test_tool_ids_none_serialization(self):
        """Test that tool_ids=None is properly handled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create agent config without tool_ids (defaults to None)
            agent_config = AgentConfig(
                id="test-agent-no-tools",
                description="Agent without specific tools",
            )
            repo.update_agent_config(agent_config)

            # Retrieve and verify tool_ids is None
            retrieved = repo.get_agent_config("test-agent-no-tools")
            assert retrieved is not None
            assert retrieved.tool_ids is None

    def test_yaml_file_location(self):
        """Test that agent configs are stored in the correct YAML file location"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create and save agent config
            agent_config = AgentConfig(id="my-agent", description="Test")
            repo.update_agent_config(agent_config)

            # Verify YAML file location is agents.yaml (directly in output_dir)
            agents_file = repo._get_agents_file()
            assert agents_file.name == "agents.yaml"
            assert agents_file.parent == repo.base_path
            assert agents_file.exists()

            # Verify the file contains the agent
            with open(agents_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert "my-agent" in data

    def test_id_field_set_on_get(self):
        """Test that id field is properly set when retrieving agent config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create and save agent config
            agent_config = AgentConfig(
                id="test-agent",
                description="Test agent",
                system_prompt="Test prompt",
            )
            repo.update_agent_config(agent_config)

            # Retrieve and verify id field is set
            retrieved = repo.get_agent_config("test-agent")
            assert retrieved is not None
            assert retrieved.id == "test-agent"
            assert retrieved.description == "Test agent"
            assert retrieved.system_prompt == "Test prompt"

    def test_id_field_set_on_list(self):
        """Test that id field is properly set when listing agent configs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileAgentConfigRepository(output_dir=output_dir)

            # Create and save multiple agent configs
            configs = [
                AgentConfig(id="agent1", description="Agent 1"),
                AgentConfig(id="agent2", description="Agent 2"),
                AgentConfig(id="agent3", description="Agent 3"),
            ]

            for config in configs:
                repo.update_agent_config(config)

            # List and verify all id fields are set
            listed_configs = repo.list_agent_configs()
            assert len(listed_configs) == 3

            for config in listed_configs:
                assert config.id is not None
                assert config.id in {"agent1", "agent2", "agent3"}
                # Verify id matches the description pattern
                if config.id == "agent1":
                    assert config.description == "Agent 1"
                elif config.id == "agent2":
                    assert config.description == "Agent 2"
                elif config.id == "agent3":
                    assert config.description == "Agent 3"
