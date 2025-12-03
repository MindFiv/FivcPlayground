#!/usr/bin/env python3
"""
Tests for FileModelConfigRepository functionality.
"""

import yaml
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
                model="gpt-4",
                description="OpenAI GPT-4 model",
                provider="openai",
                api_key="sk-test-key",
                base_url="https://api.openai.com/v1",
                temperature=0.7,
                max_tokens=2048,
            )

            # Save model config
            repo.update_model_config(model_config)

            # Verify models file exists
            models_file = repo._get_models_file()
            assert models_file.exists()

            # Retrieve model config
            retrieved_config = repo.get_model_config("gpt-4")
            assert retrieved_config is not None
            assert retrieved_config.model == "gpt-4"
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
                model="gpt-3.5",
                provider="openai",
                temperature=0.5,
            )
            repo.update_model_config(model_config)

            # Update model config
            updated_config = ModelConfig(
                id="gpt-3.5",
                model="gpt-3.5",
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
                ModelConfig(id="gpt-4", model="gpt-4", provider="openai"),
                ModelConfig(id="claude-3", model="claude-3", provider="anthropic"),
                ModelConfig(id="llama-2", model="llama-2", provider="meta"),
            ]

            for model in models:
                repo.update_model_config(model)

            # List all models
            listed_models = repo.list_model_configs()
            assert len(listed_models) == 3
            assert all(isinstance(m, ModelConfig) for m in listed_models)

            # Verify models are sorted
            model_names = [m.model for m in listed_models]
            assert model_names == sorted(model_names)

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
                model="test-model",
                provider="test-provider",
            )
            repo.update_model_config(model_config)

            # Verify model exists
            assert repo.get_model_config("test-model") is not None

            # Delete model
            repo.delete_model_config("test-model")

            # Verify model is deleted
            assert repo.get_model_config("test-model") is None

            # Verify model is not in the YAML file
            models_data = repo._load_models_data()
            assert "test-model" not in models_data

    def test_delete_nonexistent_model(self):
        """Test deleting a model that doesn't exist (should be safe)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Delete non-existent model (should not raise error)
            repo.delete_model_config("nonexistent-model")

    def test_yaml_file_format(self):
        """Test that model configs are stored in correct YAML format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create and save model config
            model_config = ModelConfig(
                id="test-model",
                model="test-model",
                description="Test description",
                provider="test-provider",
                api_key="test-key",
                temperature=0.5,
            )
            repo.update_model_config(model_config)

            # Read YAML file directly
            models_file = repo._get_models_file()
            with open(models_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Verify YAML structure - should have model_id as key
            assert "test-model" in data
            model_data = data["test-model"]
            assert model_data["id"] == "test-model"
            assert model_data["model"] == "test-model"
            assert model_data["provider"] == "test-provider"
            assert model_data["api_key"] == "test-key"
            assert model_data["temperature"] == 0.5

    def test_corrupted_yaml_handling(self):
        """Test handling of corrupted YAML files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create a corrupted YAML file
            models_file = repo._get_models_file()
            models_file.parent.mkdir(parents=True, exist_ok=True)
            with open(models_file, "w", encoding="utf-8") as f:
                f.write("{ invalid: yaml: content: [")

            # Try to load models (should return empty dict)
            models_data = repo._load_models_data()
            assert models_data == {}

            # Try to list models (should return empty list)
            models = repo.list_model_configs()
            assert models == []

    def test_model_config_with_minimal_fields(self):
        """Test model config with only required fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create model with minimal fields
            model_config = ModelConfig(
                id="minimal-model",
                model="minimal-model",
                provider="test-provider",
            )
            repo.update_model_config(model_config)

            # Retrieve and verify
            retrieved = repo.get_model_config("minimal-model")
            assert retrieved is not None
            assert retrieved.id == "minimal-model"
            assert retrieved.model == "minimal-model"
            assert retrieved.provider == "test-provider"
            assert retrieved.description is None
            assert retrieved.api_key is None
            assert retrieved.base_url is None
            assert retrieved.temperature == 0.5  # default value
            assert retrieved.max_tokens == 4096  # default value

    def test_id_field_set_on_get(self):
        """Test that id field is properly set when retrieving model config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create and save model config
            model_config = ModelConfig(
                id="test-model",
                model="test-model",
                provider="test-provider",
                temperature=0.7,
            )
            repo.update_model_config(model_config)

            # Retrieve and verify id field is set
            retrieved = repo.get_model_config("test-model")
            assert retrieved is not None
            assert retrieved.id == "test-model"
            assert retrieved.model == "test-model"
            assert retrieved.provider == "test-provider"
            assert retrieved.temperature == 0.7

    def test_id_field_set_on_list(self):
        """Test that id field is properly set when listing model configs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = OutputDir(tmpdir)
            repo = FileModelConfigRepository(output_dir=output_dir)

            # Create and save multiple model configs
            models = [
                ModelConfig(id="model1", model="model1", provider="provider1"),
                ModelConfig(id="model2", model="model2", provider="provider2"),
                ModelConfig(id="model3", model="model3", provider="provider3"),
            ]

            for model in models:
                repo.update_model_config(model)

            # List and verify all id fields are set
            listed_models = repo.list_model_configs()
            assert len(listed_models) == 3

            for model in listed_models:
                assert model.id is not None
                assert model.id in {"model1", "model2", "model3"}
                # Verify id matches the provider pattern
                if model.id == "model1":
                    assert model.provider == "provider1"
                elif model.id == "model2":
                    assert model.provider == "provider2"
                elif model.id == "model3":
                    assert model.provider == "provider3"
