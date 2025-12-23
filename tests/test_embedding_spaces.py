#!/usr/bin/env python3
"""
Tests for embedding space isolation and multi-tenancy features.

Tests verify:
- Space isolation (different spaces have separate collections)
- Backward compatibility (space_id=None uses default)
"""

import pytest
from unittest.mock import Mock, patch

from fivcplayground.embeddings.types.base import EmbeddingConfig
from fivcplayground.backends.chroma import ChromaEmbeddingDB as EmbeddingDB
from fivcplayground.tools import create_tool_retriever
from fivcplayground.tools.types.retrievers import ToolRetriever
from fivcplayground.backends.strands.tools import StrandsToolBackend


class TestEmbeddingDBSpaceIsolation:
    """Test EmbeddingDB space isolation."""

    def test_embedding_db_default_space(self):
        """Test EmbeddingDB with default space."""
        config = EmbeddingConfig(
            id="test",
            provider="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )

        with patch("fivcplayground.backends.chroma.PersistentClient"):
            with patch("fivcplayground.backends.chroma._create_embedding_function"):
                # Test with space_id=None (should default to "default")
                db = EmbeddingDB(config, space_id=None)
                assert db.space_id == "default"

                # Test with explicit "default"
                db = EmbeddingDB(config, space_id="default")
                assert db.space_id == "default"

    def test_embedding_db_custom_space(self):
        """Test EmbeddingDB with custom space."""
        config = EmbeddingConfig(
            id="test",
            provider="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )

        with patch("fivcplayground.backends.chroma.PersistentClient"):
            with patch("fivcplayground.backends.chroma._create_embedding_function"):
                db = EmbeddingDB(config, space_id="user_alice")
                assert db.space_id == "user_alice"

    def test_embedding_db_collection_naming_default(self):
        """Test collection naming for default space."""
        config = EmbeddingConfig(
            id="test",
            provider="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )

        with patch(
            "fivcplayground.backends.chroma.PersistentClient"
        ) as mock_persistent_client:
            with patch("fivcplayground.backends.chroma._create_embedding_function"):
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_persistent_client.return_value = mock_client

                db = EmbeddingDB(config, space_id="default")
                _ = db.tools  # Access tools collection

                # Should create collection named "tools" (no suffix)
                mock_client.get_or_create_collection.assert_called_once()
                call_args = mock_client.get_or_create_collection.call_args
                assert call_args[0][0] == "tools"

    def test_embedding_db_collection_naming_custom_space(self):
        """Test collection naming for custom space."""
        config = EmbeddingConfig(
            id="test",
            provider="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )

        with patch(
            "fivcplayground.backends.chroma.PersistentClient"
        ) as mock_persistent_client:
            with patch("fivcplayground.backends.chroma._create_embedding_function"):
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_persistent_client.return_value = mock_client

                db = EmbeddingDB(config, space_id="user_alice")
                _ = db.tools  # Access tools collection

                # Should create collection named "tools_user_alice"
                mock_client.get_or_create_collection.assert_called_once()
                call_args = mock_client.get_or_create_collection.call_args
                assert call_args[0][0] == "tools_user_alice"


class TestToolRetrieverSpaceIsolation:
    """Test ToolRetriever space isolation."""

    @pytest.fixture
    def mock_embedding_config_repository(self):
        """Create a mock embedding config repository."""
        mock_repo = Mock()
        mock_repo.get_embedding_config.return_value = EmbeddingConfig(
            id="default",
            provider="openai",
            model="text-embedding-ada-002",
            api_key="sk-test-key",
            base_url="https://api.openai.com/v1",
            dimension=1536,
        )
        return mock_repo

    def test_tool_retriever_default_space(self, mock_embedding_config_repository):
        """Test ToolRetriever with default space."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_db.space_id = None
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_backend=StrandsToolBackend(),
                tool_list=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Verify retriever was created successfully
            assert retriever is not None
            assert len(retriever.tools) == 0

    def test_tool_retriever_custom_space(self, mock_embedding_config_repository):
        """Test ToolRetriever with custom space."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_db.space_id = "user_alice"
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                tool_backend=StrandsToolBackend(),
                tool_list=None,
                tool_config_repository=mock_embedding_config_repository,
                embedding_db=mock_db,
            )

            # Verify retriever was created successfully
            assert retriever is not None
            assert len(retriever.tools) == 0

    def test_create_tool_retriever_default_space(self):
        """Test create_tool_retriever with default space."""
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.to_tool.return_value = Mock()
                mock_retriever.add_tool = Mock()
                mock_retriever_class.return_value = mock_retriever

                retriever = create_tool_retriever(
                    tool_backend=StrandsToolBackend(), space_id=None
                )
                assert retriever

                # Verify create_embedding_db was called with space_id=None
                mock_create_db.assert_called_once()
                call_kwargs = mock_create_db.call_args[1]
                assert call_kwargs.get("space_id") is None

                # Verify ToolRetriever was instantiated
                mock_retriever_class.assert_called_once()

    def test_create_tool_retriever_custom_space(self):
        """Test create_tool_retriever with custom space."""
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever.to_tool.return_value = Mock()
                mock_retriever.add_tool = Mock()
                mock_retriever_class.return_value = mock_retriever

                retriever = create_tool_retriever(
                    tool_backend=StrandsToolBackend(), space_id="project_website"
                )
                assert retriever

                # Verify create_embedding_db was called with space_id="project_website"
                mock_create_db.assert_called_once()
                call_kwargs = mock_create_db.call_args[1]
                assert call_kwargs.get("space_id") == "project_website"

                # Verify ToolRetriever was instantiated
                mock_retriever_class.assert_called_once()


class TestSpaceIsolationIntegration:
    """Integration tests for space isolation."""

    def test_space_id_propagation(self):
        """Test that space_id is properly propagated through the component hierarchy."""
        # Test with custom space_id
        with patch("fivcplayground.tools.create_embedding_db") as mock_create_db:
            with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
                mock_db = Mock()
                mock_db.space_id = "user_alice"
                mock_db.tools = Mock()
                mock_create_db.return_value = mock_db

                mock_retriever = Mock()
                mock_retriever_class.return_value = mock_retriever

                from fivcplayground.tools import create_tool_retriever

                retriever = create_tool_retriever(
                    tool_backend=StrandsToolBackend(),
                    space_id="user_alice",
                    load_builtin_tools=False,
                )

                # Verify space_id was passed to create_embedding_db
                mock_create_db.assert_called_once()
                call_kwargs = mock_create_db.call_args[1]
                assert call_kwargs.get("space_id") == "user_alice"

                # Verify retriever was created
                assert retriever == mock_retriever


if __name__ == "__main__":
    pytest.main([__file__])
