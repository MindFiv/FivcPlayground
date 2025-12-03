#!/usr/bin/env python3
"""
Tests for FileToolConfigRepository functionality.
"""

import yaml
import tempfile

from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.tools.types.repositories.files import FileToolConfigRepository
from fivcplayground.utils import OutputDir


class TestFileToolConfigRepository:
    """Tests for FileToolConfigRepository class"""

    def test_initialization_with_output_dir(self):
        """Test repository initialization with custom output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    def test_initialization_without_output_dir(self):
        """Test repository initialization with default output directory"""
        repo = FileToolConfigRepository()
        assert repo.base_path.exists()
        assert repo.base_path.is_dir()

    def test_update_and_get_tool_config(self):
        """Test creating and retrieving a tool configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create a tool config
            tool_config = ToolConfig(
                id="calculator",
                description="A calculator tool",
                transport="stdio",
                command="python",
                args=["calculator.py"],
            )
            repo.update_tool_config(tool_config)

            # Retrieve the tool config
            retrieved_config = repo.get_tool_config("calculator")
            assert retrieved_config is not None
            assert retrieved_config.id == "calculator"
            assert retrieved_config.description == "A calculator tool"
            assert retrieved_config.transport == "stdio"
            assert retrieved_config.command == "python"
            assert retrieved_config.args == ["calculator.py"]

    def test_update_existing_tool_config(self):
        """Test updating an existing tool configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create initial tool config
            tool_config = ToolConfig(
                id="weather",
                description="Weather tool",
                transport="sse",
                url="http://localhost:8000/sse",
            )
            repo.update_tool_config(tool_config)

            # Update tool config
            updated_config = ToolConfig(
                id="weather",
                description="Updated weather tool",
                transport="sse",
                url="http://localhost:9000/sse",
            )
            repo.update_tool_config(updated_config)

            # Verify updated config
            retrieved_config = repo.get_tool_config("weather")
            assert retrieved_config.description == "Updated weather tool"
            assert retrieved_config.url == "http://localhost:9000/sse"

    def test_list_tool_configs(self):
        """Test listing all tool configurations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create multiple tool configs
            tools = [
                ToolConfig(
                    id="tool1", description="Tool 1", transport="stdio", command="cmd1"
                ),
                ToolConfig(
                    id="tool2",
                    description="Tool 2",
                    transport="sse",
                    url="http://localhost:8000",
                ),
                ToolConfig(
                    id="tool3", description="Tool 3", transport="stdio", command="cmd3"
                ),
            ]

            for tool in tools:
                repo.update_tool_config(tool)

            # List all tools
            listed_tools = repo.list_tool_configs()
            assert len(listed_tools) == 3
            tool_ids = {tool.id for tool in listed_tools}
            assert tool_ids == {"tool1", "tool2", "tool3"}

    def test_delete_tool_config(self):
        """Test deleting a tool configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create a tool config
            tool_config = ToolConfig(
                id="test-tool",
                description="Test tool",
                transport="stdio",
                command="test",
            )
            repo.update_tool_config(tool_config)

            # Verify tool exists
            assert repo.get_tool_config("test-tool") is not None

            # Delete tool
            repo.delete_tool_config("test-tool")

            # Verify tool is deleted
            assert repo.get_tool_config("test-tool") is None
            # Verify deletion in YAML data
            tools_data = repo._load_tools_data()
            assert "test-tool" not in tools_data

    def test_delete_nonexistent_tool(self):
        """Test deleting a tool that doesn't exist (should be safe)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Delete non-existent tool (should not raise error)
            repo.delete_tool_config("nonexistent-tool")

    def test_yaml_file_format(self):
        """Test that tool configs are stored in correct YAML format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create and save tool config
            tool_config = ToolConfig(
                id="test-tool",
                description="Test description",
                transport="stdio",
                command="python",
                args=["test.py"],
            )
            repo.update_tool_config(tool_config)

            # Read YAML file directly
            tools_file = repo._get_tools_file()
            with open(tools_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Verify YAML structure - tool_id is the key
            assert "test-tool" in data
            assert data["test-tool"]["id"] == "test-tool"
            assert data["test-tool"]["description"] == "Test description"
            assert data["test-tool"]["transport"] == "stdio"

    def test_corrupted_yaml_handling(self):
        """Test handling of corrupted YAML files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create a corrupted YAML file
            tools_file = repo._get_tools_file()
            with open(tools_file, "w", encoding="utf-8") as f:
                f.write("{ invalid: yaml: content: }")

            # Try to load tools (should return empty dict)
            tools_data = repo._load_tools_data()
            assert tools_data == {}

    def test_id_field_set_on_get(self):
        """Test that id field is properly set when retrieving tool config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create and save tool config
            tool_config = ToolConfig(
                id="test-tool",
                description="Test tool",
                transport="stdio",
                command="python",
            )
            repo.update_tool_config(tool_config)

            # Retrieve and verify id field is set
            retrieved = repo.get_tool_config("test-tool")
            assert retrieved is not None
            assert retrieved.id == "test-tool"
            assert retrieved.description == "Test tool"
            assert retrieved.transport == "stdio"
            assert retrieved.command == "python"

    def test_id_field_set_on_list(self):
        """Test that id field is properly set when listing tool configs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create and save multiple tool configs
            tools = [
                ToolConfig(
                    id="tool1",
                    description="Tool 1",
                    transport="stdio",
                    command="cmd1",
                ),
                ToolConfig(
                    id="tool2",
                    description="Tool 2",
                    transport="sse",
                    url="http://localhost:8000",
                ),
                ToolConfig(
                    id="tool3",
                    description="Tool 3",
                    transport="stdio",
                    command="cmd3",
                ),
            ]

            for tool in tools:
                repo.update_tool_config(tool)

            # List and verify all id fields are set
            listed_tools = repo.list_tool_configs()
            assert len(listed_tools) == 3

            for tool in listed_tools:
                assert tool.id is not None
                assert tool.id in {"tool1", "tool2", "tool3"}
                # Verify id matches the description pattern
                if tool.id == "tool1":
                    assert tool.description == "Tool 1"
                    assert tool.transport == "stdio"
                elif tool.id == "tool2":
                    assert tool.description == "Tool 2"
                    assert tool.transport == "sse"
                elif tool.id == "tool3":
                    assert tool.description == "Tool 3"
                    assert tool.transport == "stdio"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
