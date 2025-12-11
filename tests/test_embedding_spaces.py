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
from fivcplayground.embeddings.types.backends.chroma import EmbeddingDB
from fivcplayground.tools import create_tool_retriever
from fivcplayground.tools.types.retrievers import ToolRetriever


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

        with patch("fivcplayground.embeddings.types.backends.chroma.chromadb"):
            with patch(
                "fivcplayground.embeddings.types.backends.chroma._create_embedding_function"
            ):
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

        with patch("fivcplayground.embeddings.types.backends.chroma.chromadb"):
            with patch(
                "fivcplayground.embeddings.types.backends.chroma._create_embedding_function"
            ):
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
            "fivcplayground.embeddings.types.backends.chroma.chromadb"
        ) as mock_chroma:
            with patch(
                "fivcplayground.embeddings.types.backends.chroma._create_embedding_function"
            ):
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_chroma.PersistentClient.return_value = mock_client

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
            "fivcplayground.embeddings.types.backends.chroma.chromadb"
        ) as mock_chroma:
            with patch(
                "fivcplayground.embeddings.types.backends.chroma._create_embedding_function"
            ):
                mock_client = Mock()
                mock_collection = Mock()
                mock_client.get_or_create_collection.return_value = mock_collection
                mock_chroma.PersistentClient.return_value = mock_client

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
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
                space_id=None,
            )

            assert retriever.space_id is None
            # Verify create_embedding_db was called with space_id=None
            mock_create_db.assert_called_once()
            call_kwargs = mock_create_db.call_args[1]
            assert call_kwargs.get("space_id") is None

    def test_tool_retriever_custom_space(self, mock_embedding_config_repository):
        """Test ToolRetriever with custom space."""
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            retriever = ToolRetriever(
                embedding_config_repository=mock_embedding_config_repository,
                embedding_config_id="default",
                space_id="user_alice",
            )

            assert retriever.space_id == "user_alice"
            # Verify create_embedding_db was called with space_id="user_alice"
            mock_create_db.assert_called_once()
            call_kwargs = mock_create_db.call_args[1]
            assert call_kwargs.get("space_id") == "user_alice"

    def test_create_tool_retriever_default_space(self):
        """Test create_tool_retriever with default space."""
        with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.to_tool.return_value = Mock()
            mock_retriever.add_tool = Mock()
            mock_retriever_class.return_value = mock_retriever

            retriever = create_tool_retriever(space_id=None)
            assert retriever

            # Verify ToolRetriever was instantiated with space_id=None
            mock_retriever_class.assert_called_once()
            call_kwargs = mock_retriever_class.call_args[1]
            assert call_kwargs.get("space_id") is None

    def test_create_tool_retriever_custom_space(self):
        """Test create_tool_retriever with custom space."""
        with patch("fivcplayground.tools.ToolRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.to_tool.return_value = Mock()
            mock_retriever.add_tool = Mock()
            mock_retriever_class.return_value = mock_retriever

            retriever = create_tool_retriever(space_id="project_website")
            assert retriever

            # Verify ToolRetriever was instantiated with space_id="project_website"
            mock_retriever_class.assert_called_once()
            call_kwargs = mock_retriever_class.call_args[1]
            assert call_kwargs.get("space_id") == "project_website"


class TestSpaceIsolationIntegration:
    """Integration tests for space isolation."""

    def test_space_id_propagation(self):
        """Test that space_id is properly propagated through the component hierarchy."""
        from fivcplayground.embeddings.types.base import EmbeddingConfig

        # Create embedding config
        config = EmbeddingConfig(
            id="test",
            provider="openai",
            model="text-embedding-3-small",
            api_key="sk-test-key",
        )

        # Mock the embedding config repository
        mock_repo = Mock()
        mock_repo.get_embedding_config.return_value = config

        # Test with custom space_id
        with patch("fivcplayground.embeddings.create_embedding_db") as mock_create_db:
            mock_db = Mock()
            mock_embedding_table = Mock()
            mock_embedding_table.cleanup = Mock()
            mock_db.tools = mock_embedding_table
            mock_create_db.return_value = mock_db

            from fivcplayground.tools import create_tool_retriever

            retriever = create_tool_retriever(
                embedding_config_repository=mock_repo,
                embedding_config_id="test",
                space_id="user_alice",
                load_builtin_tools=False,
            )

            # Verify space_id was passed to create_embedding_db
            mock_create_db.assert_called_once()
            call_kwargs = mock_create_db.call_args[1]
            assert call_kwargs.get("space_id") == "user_alice"

            # Verify retriever has the correct space_id
            assert retriever.space_id == "user_alice"


if __name__ == "__main__":
    pytest.main([__file__])
