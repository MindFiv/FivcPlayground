#!/usr/bin/env python3
"""
Tests for FileToolConfigRepository functionality.
"""

import json
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
            assert not repo._get_tool_file("test-tool").exists()

    def test_delete_nonexistent_tool(self):
        """Test deleting a tool that doesn't exist (should be safe)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Delete non-existent tool (should not raise error)
            repo.delete_tool_config("nonexistent-tool")

    def test_filter_repository(self):
        """Test filter_repository returns self"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Filter repository
            filtered_repo = repo.filter_repository(some_filter="value")
            assert filtered_repo is repo

    def test_json_file_format(self):
        """Test that tool configs are stored in correct JSON format"""
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

            # Read JSON file directly
            tool_file = repo._get_tool_file("test-tool")
            with open(tool_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Verify JSON structure
            assert data["id"] == "test-tool"
            assert data["description"] == "Test description"
            assert data["transport"] == "stdio"

    def test_corrupted_json_handling(self):
        """Test handling of corrupted JSON files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create a corrupted JSON file
            tool_file = repo._get_tool_file("corrupted-tool")
            tool_file.parent.mkdir(parents=True, exist_ok=True)
            with open(tool_file, "w", encoding="utf-8") as f:
                f.write("{ invalid json }")

            # Try to get corrupted tool (should return None)
            config = repo.get_tool_config("corrupted-tool")
            assert config is None


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
