"""
Tests for embeddings backend implementations.

Tests verify:
- EmbeddingDB initialization with various providers
- EmbeddingTable operations (add, search, delete, count, cleanup)
- Error handling for unsupported providers
- Metadata handling in search and delete operations
"""

from unittest.mock import Mock, patch
import pytest

from fivcplayground.embeddings.types.base import EmbeddingConfig
from fivcplayground.backends.chroma import (
    ChromaEmbeddingDB as EmbeddingDB,
    ChromaEmbeddingTable as EmbeddingTable,
    _create_embedding_function,
)


class TestCreateEmbeddingFunction:
    """Test _create_embedding_function."""

    def test_create_openai_embedding_function(self):
        """Test creating OpenAI embedding function."""
        config = EmbeddingConfig(
            id="openai-embed",
            provider="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
            base_url="https://api.openai.com/v1",
        )

        with patch(
            "fivcplayground.backends.chroma.OpenAIEmbeddingFunction"
        ) as mock_openai:
            mock_func = Mock()
            mock_openai.return_value = mock_func

            result = _create_embedding_function(config)

            assert result == mock_func
            mock_openai.assert_called_once_with(
                api_key="sk-test",
                api_base="https://api.openai.com/v1",
                model_name="text-embedding-3-small",
            )

    def test_create_ollama_embedding_function(self):
        """Test creating Ollama embedding function."""
        config = EmbeddingConfig(
            id="ollama-embed",
            provider="ollama",
            model="nomic-embed-text",
            base_url="http://localhost:11434",
        )

        with patch(
            "fivcplayground.backends.chroma.OllamaEmbeddingFunction"
        ) as mock_ollama:
            mock_func = Mock()
            mock_ollama.return_value = mock_func

            result = _create_embedding_function(config)

            assert result == mock_func
            mock_ollama.assert_called_once_with(
                url="http://localhost:11434",
                model_name="nomic-embed-text",
            )

    def test_create_embedding_function_unknown_provider(self):
        """Test creating embedding function with unknown provider."""
        config = EmbeddingConfig(
            id="unknown",
            provider="unknown_provider",
            model="model",
        )

        with pytest.raises(ValueError, match="Unknown provider"):
            _create_embedding_function(config)


class TestEmbeddingDB:
    """Test EmbeddingDB class."""

    def test_embedding_db_initialization(self):
        """Test EmbeddingDB initialization."""
        config = EmbeddingConfig(
            id="test",
            provider="openai",
            model="text-embedding-3-small",
            api_key="sk-test",
        )

        with patch("fivcplayground.backends.chroma.PersistentClient"):
            with patch(
                "fivcplayground.backends.chroma._create_embedding_function"
            ) as mock_create_func:
                mock_func = Mock()
                mock_create_func.return_value = mock_func

                db = EmbeddingDB(config)

                assert db.function == mock_func
                mock_create_func.assert_called_once_with(config)

    def test_embedding_db_getattr_creates_table(self):
        """Test that accessing attribute creates EmbeddingTable."""
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

                db = EmbeddingDB(config)
                table = db.tools

                assert isinstance(table, EmbeddingTable)
                mock_client.get_or_create_collection.assert_called_once()


class TestEmbeddingTable:
    """Test EmbeddingTable class."""

    def test_embedding_table_initialization(self):
        """Test EmbeddingTable initialization."""
        mock_collection = Mock()

        table = EmbeddingTable(mock_collection)

        assert table.collection == mock_collection
        assert table.text_splitter is not None

    def test_embedding_table_add(self):
        """Test adding text to embedding table."""
        mock_collection = Mock()
        table = EmbeddingTable(mock_collection)

        with patch.object(table.text_splitter, "split_text") as mock_split:
            mock_split.return_value = ["chunk1", "chunk2"]

            table.add("test text", metadata={"source": "test"})

            mock_collection.add.assert_called_once()
            call_args = mock_collection.add.call_args
            assert call_args[1]["documents"] == ["chunk1", "chunk2"]
            assert call_args[1]["metadatas"] == [{"source": "test"}] * 2

    def test_embedding_table_add_without_metadata(self):
        """Test adding text without metadata."""
        mock_collection = Mock()
        table = EmbeddingTable(mock_collection)

        with patch.object(table.text_splitter, "split_text") as mock_split:
            mock_split.return_value = ["chunk1"]

            table.add("test text")

            call_args = mock_collection.add.call_args
            assert call_args[1]["metadatas"] is None

    def test_embedding_table_search(self):
        """Test searching embedding table."""
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"id": "1"}, {"id": "2"}]],
            "distances": [[0.1, 0.2]],
        }

        table = EmbeddingTable(mock_collection)
        results = table.search("query", num_documents=10)

        assert len(results) == 2
        assert results[0]["text"] == "doc1"
        assert results[0]["metadata"] == {"id": "1"}
        assert results[0]["score"] == 0.1

    def test_embedding_table_delete_with_metadata(self):
        """Test deleting from embedding table with metadata."""
        mock_collection = Mock()
        table = EmbeddingTable(mock_collection)

        table.delete({"source": "test"})

        mock_collection.delete.assert_called_once()
        call_args = mock_collection.delete.call_args
        assert "where" in call_args[1]

    def test_embedding_table_delete_without_metadata(self):
        """Test deleting without metadata raises error."""
        mock_collection = Mock()
        table = EmbeddingTable(mock_collection)

        with pytest.raises(ValueError, match="metadata is required"):
            table.delete({})

    def test_embedding_table_count(self):
        """Test counting documents in table."""
        mock_collection = Mock()
        mock_collection.count.return_value = 42

        table = EmbeddingTable(mock_collection)
        count = table.count()

        assert count == 42

    def test_embedding_table_cleanup(self):
        """Test cleanup removes all documents."""
        mock_collection = Mock()
        mock_collection.peek.side_effect = [
            {"ids": ["id1", "id2"]},
            {"ids": []},
        ]

        table = EmbeddingTable(mock_collection)
        table.cleanup()

        mock_collection.delete.assert_called_once_with(ids=["id1", "id2"])
