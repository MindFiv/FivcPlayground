#!/usr/bin/env python3
"""
Tests for the embeddings module.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from fivcplayground.embeddings.types.db import EmbeddingDB, EmbeddingCollection


class TestEmbeddingCollection:
    """Test the EmbeddingCollection class."""

    @pytest.fixture
    def mock_chroma_collection(self):
        """Create a mock Chroma collection."""
        mock_collection = Mock()
        mock_collection.add = Mock()
        mock_collection.query = Mock(
            return_value={
                "documents": [["doc1", "doc2"]],
                "metadatas": [[{"key": "value1"}, {"key": "value2"}]],
                "distances": [[0.1, 0.2]],
            }
        )
        mock_collection.count = Mock(return_value=2)
        mock_collection.delete = Mock()
        mock_collection.peek = Mock(return_value={"ids": []})
        return mock_collection

    def test_init(self, mock_chroma_collection):
        """Test EmbeddingCollection initialization."""
        collection = EmbeddingCollection(mock_chroma_collection)

        assert collection.collection == mock_chroma_collection
        assert collection.text_splitter is not None

    def test_add_document(self, mock_chroma_collection):
        """Test adding a document."""
        collection = EmbeddingCollection(mock_chroma_collection)

        collection.add("test document", metadata={"key": "value"})

        mock_chroma_collection.add.assert_called_once()
        call_args = mock_chroma_collection.add.call_args[1]
        assert "documents" in call_args
        assert "metadatas" in call_args
        assert "ids" in call_args

    def test_search(self, mock_chroma_collection):
        """Test searching documents."""
        collection = EmbeddingCollection(mock_chroma_collection)

        results = collection.search("query", num_documents=2)

        assert len(results) == 2
        assert results[0]["text"] == "doc1"
        assert results[0]["metadata"] == {"key": "value1"}
        assert results[0]["score"] == 0.1
        assert results[1]["text"] == "doc2"
        assert results[1]["metadata"] == {"key": "value2"}
        assert results[1]["score"] == 0.2
        mock_chroma_collection.query.assert_called_once()

    def test_count(self, mock_chroma_collection):
        """Test counting documents."""
        collection = EmbeddingCollection(mock_chroma_collection)

        count = collection.count()

        assert count == 2
        mock_chroma_collection.count.assert_called_once()

    def test_clear(self, mock_chroma_collection):
        """Test clearing collection."""
        collection = EmbeddingCollection(mock_chroma_collection)
        # First call returns IDs, second call returns empty
        mock_chroma_collection.peek = Mock(
            side_effect=[
                {"ids": ["id1", "id2"]},
                {"ids": []},
            ]
        )

        collection.clear()

        mock_chroma_collection.delete.assert_called_once()
        assert mock_chroma_collection.peek.call_count == 2


class TestEmbeddingDB:
    """Test the EmbeddingDB class."""

    @pytest.fixture
    def mock_embedding_function(self):
        """Create a mock embedding function."""
        return Mock()

    @pytest.fixture
    def mock_chroma_client(self):
        """Create a mock Chroma client."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.add = Mock()
        mock_collection.query = Mock(
            return_value={
                "documents": [["doc1"]],
            }
        )
        mock_collection.count = Mock(return_value=1)
        mock_collection.peek = Mock(return_value={"ids": []})
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        return mock_client

    @patch("fivcplayground.embeddings.types.db.chromadb.PersistentClient")
    def test_init(self, mock_chroma_class, mock_embedding_function):
        """Test EmbeddingDB initialization."""
        mock_client = Mock()
        mock_chroma_class.return_value = mock_client

        db = EmbeddingDB(function=mock_embedding_function)

        assert db.function == mock_embedding_function
        assert db.db == mock_client
        mock_chroma_class.assert_called_once()

    @patch("fivcplayground.embeddings.types.db.chromadb.PersistentClient")
    def test_get_collection(self, mock_chroma_class, mock_embedding_function):
        """Test getting a collection."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection = Mock(return_value=mock_collection)
        mock_chroma_class.return_value = mock_client

        db = EmbeddingDB(function=mock_embedding_function)
        collection = db.get_collection("test_collection")

        assert isinstance(collection, EmbeddingCollection)
        mock_client.get_or_create_collection.assert_called_once_with(
            "test_collection", embedding_function=mock_embedding_function
        )


class TestCreateEmbeddingFunction:
    """Test the create_embedding_function function."""

    @patch("fivcplayground.embeddings._openai_embedding_function")
    @patch(
        "fivcplayground.embeddings.settings.DEFAULT_EMBEDDING_ARGS",
        new_callable=MagicMock,
    )
    def test_create_embedding_function_openai(self, mock_config, mock_openai):
        """Test creating an OpenAI embedding function."""
        from fivcplayground.embeddings import create_embedding_function

        # Mock DEFAULT_EMBEDDING_ARGS to return a dict when called
        mock_config.return_value = {
            "provider": "openai",
            "model": "text-embedding-ada-002",
        }
        mock_func = Mock()
        mock_openai.return_value = mock_func

        func = create_embedding_function()

        assert func == mock_func
        mock_openai.assert_called_once()

    @patch("fivcplayground.embeddings._ollama_embedding_function")
    @patch(
        "fivcplayground.embeddings.settings.DEFAULT_EMBEDDING_ARGS",
        new_callable=MagicMock,
    )
    def test_create_embedding_function_ollama(self, mock_config, mock_ollama):
        """Test creating an Ollama embedding function."""
        from fivcplayground.embeddings import create_embedding_function

        # Mock DEFAULT_EMBEDDING_ARGS to return a dict when called
        mock_config.return_value = {"provider": "ollama", "model": "llama2"}
        mock_func = Mock()
        mock_ollama.return_value = mock_func

        func = create_embedding_function()

        assert func == mock_func
        mock_ollama.assert_called_once()

    @patch("chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction")
    @patch(
        "fivcplayground.embeddings.settings.DEFAULT_EMBEDDING_ARGS",
        new_callable=MagicMock,
    )
    def test_create_embedding_function_default(self, mock_config, mock_sentence):
        """Test creating a default (sentence transformer) embedding function."""
        from fivcplayground.embeddings import create_embedding_function

        # Mock DEFAULT_EMBEDDING_ARGS to return a dict with provider when called
        mock_config.return_value = {"provider": "other"}
        mock_func = Mock()
        mock_sentence.return_value = mock_func

        func = create_embedding_function()

        assert func == mock_func
        mock_sentence.assert_called_once_with(model_name="all-MiniLM-L6-v2")

    @patch(
        "fivcplayground.embeddings.settings.DEFAULT_EMBEDDING_ARGS",
        new_callable=MagicMock,
    )
    def test_create_embedding_function_no_provider(self, mock_config):
        """Test that create_embedding_function raises error without provider."""
        from fivcplayground.embeddings import create_embedding_function

        # Mock DEFAULT_EMBEDDING_ARGS to return a dict without provider when called
        mock_config.return_value = {"provider": None}

        with pytest.raises(AssertionError, match="provider not specified"):
            create_embedding_function()


class TestCreateEmbeddingDB:
    """Test the create_embedding_db function."""

    @patch("fivcplayground.embeddings.EmbeddingDB")
    @patch("fivcplayground.embeddings.create_embedding_function")
    def test_create_embedding_db_default(self, mock_create_func, mock_db_class):
        """Test creating an embedding DB with default function."""
        from fivcplayground.embeddings import create_embedding_db

        mock_func = Mock()
        mock_create_func.return_value = mock_func
        mock_db = Mock()
        mock_db_class.return_value = mock_db

        db = create_embedding_db()

        assert db == mock_db
        mock_create_func.assert_called_once()
        mock_db_class.assert_called_once()

    @patch("fivcplayground.embeddings.EmbeddingDB")
    def test_create_embedding_db_custom_function(self, mock_db_class):
        """Test creating an embedding DB with custom function."""
        from fivcplayground.embeddings import create_embedding_db

        mock_func = Mock()
        mock_db = Mock()
        mock_db_class.return_value = mock_db

        db = create_embedding_db(function=mock_func)

        assert db == mock_db
        mock_db_class.assert_called_once()
        call_kwargs = mock_db_class.call_args[1]
        assert call_kwargs["function"] == mock_func


if __name__ == "__main__":
    pytest.main([__file__])
