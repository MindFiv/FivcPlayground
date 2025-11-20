#!/usr/bin/env python3
"""
Tests for FileModelConfigRepository functionality.
"""

import json
import tempfile

from fivcplayground.models.types.base import ModelConfig
from fivcplayground.models.types.repositories.files import FileModelConfigRepository
from fivcplayground.utils import OutputDir


class TestFileModelConfigRepository:
    """Tests for FileModelConfigRepository class"""

    def test_initialization_with_output_dir(self):
        """Test repository initialization with custom output directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            assert repo.output_dir == output_dir
            assert repo.base_path.exists()
            assert repo.base_path.is_dir()

    def test_initialization_without_output_dir(self):
        """Test repository initialization with default output directory"""
        repo = FileModelConfigRepository()
        assert repo.base_path.exists()
        assert repo.base_path.is_dir()

    def test_update_and_get_model_config(self):
        """Test creating and retrieving a model configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create a model config
            model_config = ModelConfig(
                id="gpt-4",
                model_id="gpt-4",
                description="OpenAI GPT-4 model",
                provider="openai",
                api_key="sk-test-key",
                base_url="https://api.openai.com/v1",
                temperature=0.7,
                max_tokens=2048,
            )

            # Save model config
            repo.update_model_config(model_config)

            # Verify model file exists
            model_file = repo._get_model_file("gpt-4")
            assert model_file.exists()

            # Retrieve model config
            retrieved_config = repo.get_model_config("gpt-4")
            assert retrieved_config is not None
            assert retrieved_config.model_id == "gpt-4"
            assert retrieved_config.provider == "openai"
            assert retrieved_config.api_key == "sk-test-key"
            assert retrieved_config.temperature == 0.7
            assert retrieved_config.max_tokens == 2048

    def test_get_nonexistent_model(self):
        """Test retrieving a model that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Try to get non-existent model
            config = repo.get_model_config("nonexistent-model")
            assert config is None

    def test_update_existing_model_config(self):
        """Test updating an existing model configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create initial model config
            model_config = ModelConfig(
                id="gpt-3.5",
                model_id="gpt-3.5",
                provider="openai",
                temperature=0.5,
            )
            repo.update_model_config(model_config)

            # Update model config
            updated_config = ModelConfig(
                id="gpt-3.5",
                model_id="gpt-3.5",
                provider="openai",
                temperature=0.8,
                max_tokens=4096,
            )
            repo.update_model_config(updated_config)

            # Verify updated config
            retrieved_config = repo.get_model_config("gpt-3.5")
            assert retrieved_config.temperature == 0.8
            assert retrieved_config.max_tokens == 4096

    def test_list_model_configs(self):
        """Test listing all model configurations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create multiple model configs
            models = [
                ModelConfig(id="gpt-4", model_id="gpt-4", provider="openai"),
                ModelConfig(id="claude-3", model_id="claude-3", provider="anthropic"),
                ModelConfig(id="llama-2", model_id="llama-2", provider="meta"),
            ]

            for model in models:
                repo.update_model_config(model)

            # List all models
            listed_models = repo.list_model_configs()
            assert len(listed_models) == 3
            assert all(isinstance(m, ModelConfig) for m in listed_models)

            # Verify models are sorted
            model_ids = [m.model_id for m in listed_models]
            assert model_ids == sorted(model_ids)

    def test_list_empty_repository(self):
        """Test listing models from empty repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # List models from empty repository
            models = repo.list_model_configs()
            assert models == []

    def test_delete_model_config(self):
        """Test deleting a model configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create a model config
            model_config = ModelConfig(
                id="test-model",
                model_id="test-model",
                provider="test-provider",
            )
            repo.update_model_config(model_config)

            # Verify model exists
            assert repo.get_model_config("test-model") is not None

            # Delete model
            repo.delete_model_config("test-model")

            # Verify model is deleted
            assert repo.get_model_config("test-model") is None
            assert not repo._get_model_file("test-model").exists()

    def test_delete_nonexistent_model(self):
        """Test deleting a model that doesn't exist (should be safe)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Delete non-existent model (should not raise error)
            repo.delete_model_config("nonexistent-model")

    def test_filter_repository(self):
        """Test filter_repository returns self"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Filter repository
            filtered_repo = repo.filter_repository(some_filter="value")
            assert filtered_repo is repo

    def test_json_file_format(self):
        """Test that model configs are stored in correct JSON format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create and save model config
            model_config = ModelConfig(
                id="test-model",
                model_id="test-model",
                description="Test description",
                provider="test-provider",
                api_key="test-key",
                temperature=0.5,
            )
            repo.update_model_config(model_config)

            # Read JSON file directly
            model_file = repo._get_model_file("test-model")
            with open(model_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Verify JSON structure
            assert data["id"] == "test-model"
            assert data["model_id"] == "test-model"
            assert data["provider"] == "test-provider"
            assert data["api_key"] == "test-key"
            assert data["temperature"] == 0.5

    def test_corrupted_json_handling(self):
        """Test handling of corrupted JSON files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create a corrupted JSON file
            model_file = repo._get_model_file("corrupted-model")
            model_file.parent.mkdir(parents=True, exist_ok=True)
            with open(model_file, "w", encoding="utf-8") as f:
                f.write("{ invalid json }")

            # Try to get corrupted model (should return None)
            config = repo.get_model_config("corrupted-model")
            assert config is None

    def test_model_config_with_minimal_fields(self):
        """Test model config with only required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create model with minimal fields
            model_config = ModelConfig(
                id="minimal-model",
                model_id="minimal-model",
                provider="test-provider",
            )
            repo.update_model_config(model_config)

            # Retrieve and verify
            retrieved = repo.get_model_config("minimal-model")
            assert retrieved is not None
            assert retrieved.id == "minimal-model"
            assert retrieved.model_id == "minimal-model"
            assert retrieved.provider == "test-provider"
            assert retrieved.description is None
            assert retrieved.api_key is None
            assert retrieved.base_url is None
            assert retrieved.temperature == 0.5  # default value
            assert retrieved.max_tokens == 4096  # default value
