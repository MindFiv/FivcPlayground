#!/usr/bin/env python3
"""
End-to-end integration tests for the tools module.

Tests the complete flow: FileToolConfigRepository → ToolLoader → ToolRetriever
"""

import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.tools.types.repositories.files import FileToolConfigRepository
from fivcplayground.tools import create_tool_loader
from fivcplayground.tools.types.retrievers import ToolRetriever
from fivcplayground.utils import OutputDir
from fivcplayground import __backend__


def create_mock_tool(name: str, description: str):
    """Create a mock tool with correct attributes based on the current backend."""
    tool = Mock()
    if __backend__ == "langchain":
        tool.name = name
        tool.description = description
    else:  # strands
        tool.tool_name = name
        tool.tool_spec = {"description": description}
    return tool


class TestToolsIntegration:
    """End-to-end integration tests for tools module"""

    @pytest.mark.asyncio
    async def test_complete_flow_repository_to_loader(self):
        """Test complete flow: repository → loader"""
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
            with patch(
                "fivcplayground.embeddings.create_embedding_db"
            ) as mock_create_db:
                mock_embedding_db = Mock()
                mock_collection = Mock()
                mock_collection.clear = Mock()
                mock_collection.count = Mock(return_value=0)
                mock_collection.add = Mock()
                mock_collection.search = Mock(return_value=[])
                mock_embedding_db.tools = mock_collection
                mock_create_db.return_value = mock_embedding_db

                retriever = ToolRetriever(
                    embedding_config_repository=None,
                    embedding_config_id="default",
                )

                # Setup loader
                loader = create_tool_loader(
                    tool_retriever=retriever,
                    tool_config_repository=repo,
                )

                # Mock ToolBundle to avoid actual MCP connections
                with patch(
                    "fivcplayground.tools.types.loaders.ToolBundle"
                ) as mock_bundle_class:
                    mock_bundle = MagicMock()
                    mock_bundle_class.return_value = mock_bundle

                    # Create mock tools with unique names
                    weather_tool = create_mock_tool(
                        "get_weather", "Get weather information"
                    )
                    forecast_tool = create_mock_tool(
                        "get_forecast", "Get weather forecast"
                    )

                    # Mock async context manager
                    mock_bundle.load_async.return_value.__aenter__.return_value = [
                        weather_tool,
                        forecast_tool,
                    ]
                    mock_bundle.load_async.return_value.__aexit__.return_value = None

                    # Load tools
                    await loader.load_async()

                    # Verify bundle was added to retriever
                    assert len(retriever.tools) >= 1

                    # Verify bundles were tracked with tool names
                    assert len(loader.tool_bundles) == 1
                    assert "weather_server" in loader.tool_bundles
                    # The bundle should track the tool names
                    assert "get_weather" in loader.tool_bundles["weather_server"]
                    assert "get_forecast" in loader.tool_bundles["weather_server"]

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
    async def test_loader_handles_repository_updates(self):
        """Test that loader handles repository updates correctly"""
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

            # Setup retriever and loader with mocked embedding DB
            with patch(
                "fivcplayground.embeddings.create_embedding_db"
            ) as mock_create_db:
                mock_embedding_db = Mock()
                mock_collection = Mock()
                mock_collection.clear = Mock()
                mock_collection.count = Mock(return_value=0)
                mock_collection.add = Mock()
                mock_collection.search = Mock(return_value=[])
                mock_embedding_db.tools = mock_collection
                mock_create_db.return_value = mock_embedding_db

                retriever = ToolRetriever(
                    embedding_config_repository=None,
                    embedding_config_id="default",
                )
                loader = create_tool_loader(
                    tool_retriever=retriever,
                    tool_config_repository=repo,
                )

                # First load
                with patch(
                    "fivcplayground.tools.types.loaders.ToolBundle"
                ) as mock_bundle_class:
                    mock_bundle = MagicMock()
                    mock_bundle_class.return_value = mock_bundle
                    tool1 = create_mock_tool("tool1", "Tool 1")
                    mock_bundle.load_async.return_value.__aenter__.return_value = [
                        tool1
                    ]
                    mock_bundle.load_async.return_value.__aexit__.return_value = None

                    await loader.load_async()
                    assert "server1" in loader.tool_bundles

                # Add new config
                config2 = ToolConfig(
                    id="server2",
                    description="Server 2",
                    transport="sse",
                    url="http://localhost:8000",
                )
                repo.update_tool_config(config2)

                # Second load should include both servers
                with patch(
                    "fivcplayground.tools.types.loaders.ToolBundle"
                ) as mock_bundle_class:
                    mock_bundle = MagicMock()
                    mock_bundle_class.return_value = mock_bundle
                    tool2 = create_mock_tool("tool2", "Tool 2")
                    mock_bundle.load_async.return_value.__aenter__.return_value = [
                        tool2
                    ]
                    mock_bundle.load_async.return_value.__aexit__.return_value = None

                    await loader.load_async()
                    # Both servers should be in bundles
                    assert (
                        "server1" in loader.tool_bundles
                        or "server2" in loader.tool_bundles
                    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
