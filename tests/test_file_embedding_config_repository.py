#!/usr/bin/env python3
"""
Tests for FileEmbeddingConfigRepository functionality and EmbeddingDB/EmbeddingTable integration.
"""

import yaml
import tempfile

from fivcplayground.embeddings.types.base import EmbeddingConfig
from fivcplayground.embeddings.types.repositories.files import (
    FileEmbeddingConfigRepository,
)
from fivcplayground.embeddings import create_embedding_db, EmbeddingDB, EmbeddingTable
from fivcplayground.backends.chroma import ChromaEmbeddingBackend
from fivcplayground.utils import OutputDir


class TestFileEmbeddingConfigRepository:
    """Tests for FileEmbeddingConfigRepository class"""

    def test_initialization_with_output_dir(self):
        """Test repository initialization with custom output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    def test_initialization_without_output_dir(self):
        """Test repository initialization with default output directory"""
        repo = FileEmbeddingConfigRepository()
        assert repo.base_path.exists()
        assert repo.base_path.is_dir()

    def test_update_and_get_embedding_config(self):
        """Test creating and retrieving an embedding configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # Create an embedding config
            embedding_config = EmbeddingConfig(
                id="openai-ada",
                provider="openai",
                model="text-embedding-ada-002",
                api_key="sk-test-key",
                base_url="https://api.openai.com/v1",
                dimension=1536,
            )

            # Save embedding config
            repo.update_embedding_config(embedding_config)

            # Verify embeddings file exists
            embeddings_file = repo._get_embeddings_file()
            assert embeddings_file.exists()

            # Retrieve embedding config
            retrieved_config = repo.get_embedding_config("openai-ada")
            assert retrieved_config is not None
            assert retrieved_config.model == "text-embedding-ada-002"
            assert retrieved_config.provider == "openai"
            assert retrieved_config.api_key == "sk-test-key"
            assert retrieved_config.dimension == 1536

    def test_update_existing_embedding_config(self):
        """Test updating an existing embedding configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # Create initial embedding config
            embedding_config = EmbeddingConfig(
                id="test-embedding",
                provider="openai",
                model="text-embedding-3-small",
                dimension=1536,
            )
            repo.update_embedding_config(embedding_config)

            # Update embedding config
            updated_config = EmbeddingConfig(
                id="test-embedding",
                provider="openai",
                model="text-embedding-3-large",
                dimension=3072,
            )
            repo.update_embedding_config(updated_config)

            # Verify updated config
            retrieved_config = repo.get_embedding_config("test-embedding")
            assert retrieved_config.model == "text-embedding-3-large"
            assert retrieved_config.dimension == 3072

    def test_list_embedding_configs(self):
        """Test listing all embedding configurations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # Create multiple embedding configs
            embeddings = [
                EmbeddingConfig(
                    id="openai-ada",
                    provider="openai",
                    model="text-embedding-ada-002",
                ),
                EmbeddingConfig(
                    id="ollama-nomic", provider="ollama", model="nomic-embed-text"
                ),
                EmbeddingConfig(
                    id="sentence-transformer",
                    provider="huggingface",
                    model="all-MiniLM-L6-v2",
                ),
            ]

            for embedding in embeddings:
                repo.update_embedding_config(embedding)

            # List all embeddings
            listed_embeddings = repo.list_embedding_configs()
            assert len(listed_embeddings) == 3
            assert all(isinstance(e, EmbeddingConfig) for e in listed_embeddings)

    def test_list_empty_repository(self):
        """Test listing embeddings from empty repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # List embeddings from empty repository
            embeddings = repo.list_embedding_configs()
            assert embeddings == []

    def test_delete_embedding_config(self):
        """Test deleting an embedding configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # Create an embedding config
            embedding_config = EmbeddingConfig(
                id="test-embedding",
                provider="openai",
                model="text-embedding-ada-002",
            )
            repo.update_embedding_config(embedding_config)

            # Verify embedding exists
            assert repo.get_embedding_config("test-embedding") is not None

            # Delete embedding
            repo.delete_embedding_config("test-embedding")

            # Verify embedding is deleted
            assert repo.get_embedding_config("test-embedding") is None

            # Verify embedding is not in the YAML file
            embeddings_data = repo._load_embeddings_data()
            assert "test-embedding" not in embeddings_data

    def test_delete_nonexistent_embedding(self):
        """Test deleting an embedding that doesn't exist (should be safe)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # Delete non-existent embedding (should not raise error)
            repo.delete_embedding_config("nonexistent-embedding")

    def test_yaml_file_format(self):
        """Test that embedding configs are stored in correct YAML format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # Create and save embedding config
            embedding_config = EmbeddingConfig(
                id="test-embedding",
                description="Test embedding",
                provider="openai",
                model="text-embedding-ada-002",
                api_key="sk-test",
                base_url="https://api.openai.com/v1",
                dimension=1536,
            )
            repo.update_embedding_config(embedding_config)

            # Read YAML file directly
            embeddings_file = repo._get_embeddings_file()
            with open(embeddings_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Verify YAML structure - should have embedding_id as key
            assert "test-embedding" in data
            embedding_data = data["test-embedding"]
            assert embedding_data["id"] == "test-embedding"
            assert embedding_data["description"] == "Test embedding"
            assert embedding_data["provider"] == "openai"
            assert embedding_data["model"] == "text-embedding-ada-002"
            assert embedding_data["api_key"] == "sk-test"
            assert embedding_data["dimension"] == 1536

    def test_id_field_set_on_get(self):
        """Test that id field is properly set when retrieving embedding config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # Create and save embedding config
            embedding_config = EmbeddingConfig(
                id="test-embedding",
                provider="openai",
                model="text-embedding-ada-002",
                dimension=1536,
            )
            repo.update_embedding_config(embedding_config)

            # Retrieve and verify id field is set
            retrieved = repo.get_embedding_config("test-embedding")
            assert retrieved is not None
            assert retrieved.id == "test-embedding"
            assert retrieved.provider == "openai"
            assert retrieved.model == "text-embedding-ada-002"
            assert retrieved.dimension == 1536

    def test_id_field_set_on_list(self):
        """Test that id field is properly set when listing embedding configs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            # Create and save multiple embedding configs
            embeddings = [
                EmbeddingConfig(
                    id="embedding1",
                    provider="openai",
                    model="text-embedding-ada-002",
                ),
                EmbeddingConfig(
                    id="embedding2",
                    provider="ollama",
                    model="nomic-embed-text",
                ),
                EmbeddingConfig(
                    id="embedding3",
                    provider="huggingface",
                    model="all-MiniLM-L6-v2",
                ),
            ]

            for embedding in embeddings:
                repo.update_embedding_config(embedding)

            # List and verify all id fields are set
            listed_embeddings = repo.list_embedding_configs()
            assert len(listed_embeddings) == 3

            for embedding in listed_embeddings:
                assert embedding.id is not None
                assert embedding.id in {"embedding1", "embedding2", "embedding3"}
                # Verify id matches the provider pattern
                if embedding.id == "embedding1":
                    assert embedding.provider == "openai"
                elif embedding.id == "embedding2":
                    assert embedding.provider == "ollama"
                elif embedding.id == "embedding3":
                    assert embedding.provider == "huggingface"


class TestEmbeddingDBIntegration:
    """Tests for EmbeddingDB and EmbeddingTable integration with new API"""

    def test_create_embedding_db_with_config(self):
        """Test creating EmbeddingDB with EmbeddingConfig"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save embedding config
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            embedding_config = EmbeddingConfig(
                id="default",
                provider="openai",
                model="text-embedding-ada-002",
                api_key="sk-test-key",
                base_url="https://api.openai.com/v1",
                dimension=1536,
            )
            repo.update_embedding_config(embedding_config)

            # Create EmbeddingDB using factory function
            db = create_embedding_db(
                embedding_backend=ChromaEmbeddingBackend(),
                embedding_config_repository=repo,
                embedding_config_id="default",
            )

            assert isinstance(db, EmbeddingDB)

    def test_embedding_table_dynamic_access(self):
        """Test accessing EmbeddingTable via dynamic attribute access"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create and save embedding config
            output_dir = OutputDir(tmpdir)
            repo = FileEmbeddingConfigRepository(output_dir=output_dir)

            embedding_config = EmbeddingConfig(
                id="default",
                provider="openai",
                model="text-embedding-ada-002",
                api_key="sk-test-key",
                base_url="https://api.openai.com/v1",
                dimension=1536,
            )
            repo.update_embedding_config(embedding_config)

            # Create EmbeddingDB and access collection via dynamic attribute
            db = create_embedding_db(
                embedding_backend=ChromaEmbeddingBackend(),
                embedding_config_repository=repo,
                embedding_config_id="default",
            )

            # Access collection using dynamic attribute (e.g., db.my_collection)
            collection = db.my_collection
            assert isinstance(collection, EmbeddingTable)
