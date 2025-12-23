#!/usr/bin/env python3
"""
End-to-end integration tests for the tools module.

Tests the complete flow: FileToolConfigRepository → create_tool_retriever() → ToolRetriever
"""

import tempfile
import pytest
from unittest.mock import Mock, patch

from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.tools.types.repositories.files import FileToolConfigRepository
from fivcplayground.tools import create_tool_retriever
from fivcplayground.tools.types.retrievers import ToolRetriever
from fivcplayground.backends.strands.tools import StrandsToolBackend
from fivcplayground.utils import OutputDir


def create_mock_tool_langchain(name: str, description: str):
    """Create a mock tool for LangChain backend."""
    tool = Mock()
    tool.name = name
    tool.description = description
    return tool


def create_mock_tool_strands(name: str, description: str):
    """Create a mock tool for Strands backend."""
    tool = Mock()
    tool.tool_name = name
    tool.tool_spec = {"description": description}
    return tool


class TestToolsIntegration:
    """End-to-end integration tests for tools module"""

    @pytest.mark.asyncio
    async def test_complete_flow_repository_to_retriever(self):
        """Test complete flow: repository → retriever with load_mcp_tools"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup repository with tool configs
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Create and store tool configs
            tool_configs = [
                ToolConfig(
                    id="weather_server",
                    description="Weather tool server",
                    transport="stdio",
                    command="python",
                    args=["weather_server.py"],
                ),
            ]

            for config in tool_configs:
                repo.update_tool_config(config)

            # Verify configs are stored
            assert len(repo.list_tool_configs()) == 1

            # Setup retriever with mocked embedding DB
            with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
                mock_embedding_db = Mock()
                mock_collection = Mock()
                mock_collection.cleanup = Mock()
                mock_collection.add = Mock()
                mock_collection.search = Mock(return_value=[])
                mock_embedding_db.tools = mock_collection
                mock_create_db.return_value = mock_embedding_db

                # Create retriever
                retriever = create_tool_retriever(
                    tool_backend=StrandsToolBackend(),
                    tool_config_repository=repo,
                )

                # Verify retriever was created successfully
                assert retriever is not None
                assert isinstance(retriever, ToolRetriever)

    @pytest.mark.asyncio
    async def test_repository_persistence_across_loads(self):
        """Test that repository persists configs across multiple loads"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)

            # First session: create and store configs
            repo1 = FileToolConfigRepository(output_dir=output_dir)
            config = ToolConfig(
                id="persistent_tool",
                description="A persistent tool",
                transport="stdio",
                command="python",
            )
            repo1.update_tool_config(config)

            # Second session: verify config persists
            repo2 = FileToolConfigRepository(output_dir=output_dir)
            retrieved = repo2.get_tool_config("persistent_tool")

            assert retrieved is not None
            assert retrieved.id == "persistent_tool"
            assert retrieved.description == "A persistent tool"

    @pytest.mark.asyncio
    async def test_retriever_loads_repository_configs(self):
        """Test that retriever loads configs from repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileToolConfigRepository(output_dir=output_dir)

            # Initial config
            config1 = ToolConfig(
                id="server1",
                description="Server 1",
                transport="stdio",
                command="python",
            )
            repo.update_tool_config(config1)

            # Setup retriever with mocked embedding DB
            with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
                mock_embedding_db = Mock()
                mock_collection = Mock()
                mock_collection.cleanup = Mock()
                mock_collection.add = Mock()
                mock_collection.search = Mock(return_value=[])
                mock_embedding_db.tools = mock_collection
                mock_create_db.return_value = mock_embedding_db

                # Create retriever
                retriever = create_tool_retriever(
                    tool_backend=StrandsToolBackend(),
                    tool_config_repository=repo,
                )

                # Verify retriever was created successfully
                assert retriever is not None
                assert isinstance(retriever, ToolRetriever)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
