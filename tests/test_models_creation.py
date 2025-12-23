"""
Tests for model creation functions in fivcplayground.models module.

Tests verify:
- create_model with various model config IDs
- create_chat_model, create_reasoning_model, create_coding_model
- Error handling for missing configs
- Model backend creation
"""

from unittest.mock import Mock, patch
import pytest

from fivcplayground.models import (
    create_model,
    # create_chat_model,
    # create_reasoning_model,
    # create_coding_model,
)
from fivcplayground.models.types.base import ModelConfig


class TestCreateModel:
    """Test create_model function."""

    def test_create_model_with_valid_config(self):
        """Test creating model with valid configuration."""
        mock_model = Mock()
        mock_model_config = ModelConfig(
            id="test-model",
            provider="openai",
            model="gpt-4o-mini",
        )
        mock_model_repo = Mock()
        mock_model_repo.get_model_config.return_value = mock_model_config

        mock_backend = Mock()
        mock_backend.create_model.return_value = mock_model

        result = create_model(
            model_backend=mock_backend,
            model_config_repository=mock_model_repo,
            model_config_id="test-model",
        )

        assert result == mock_model
        mock_model_repo.get_model_config.assert_called_once_with("test-model")
        mock_backend.create_model.assert_called_once_with(mock_model_config)

    def test_create_model_missing_config(self):
        """Test create_model raises error when config not found."""
        mock_model_repo = Mock()
        mock_model_repo.get_model_config.return_value = None

        mock_backend = Mock()

        with pytest.raises(ValueError, match="Default model not found"):
            create_model(
                model_backend=mock_backend, model_config_repository=mock_model_repo
            )

    def test_create_model_default_config_id(self):
        """Test create_model uses 'default' as default config ID."""
        mock_model = Mock()
        mock_model_config = ModelConfig(
            id="default",
            provider="openai",
            model="gpt-4o-mini",
        )
        mock_model_repo = Mock()
        mock_model_repo.get_model_config.return_value = mock_model_config

        mock_backend = Mock()
        mock_backend.create_model.return_value = mock_model

        create_model(
            model_backend=mock_backend, model_config_repository=mock_model_repo
        )

        mock_model_repo.get_model_config.assert_called_once_with("default")

    def test_create_model_passes_config_to_backend(self):
        """Test create_model passes config to backend create function."""
        mock_model = Mock()
        mock_model_config = ModelConfig(
            id="test",
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
        )
        mock_model_repo = Mock()
        mock_model_repo.get_model_config.return_value = mock_model_config

        mock_backend = Mock()
        mock_backend.create_model.return_value = mock_model

        create_model(
            model_backend=mock_backend, model_config_repository=mock_model_repo
        )

        # Verify the config was passed to backend
        mock_backend.create_model.assert_called_once()
        passed_config = mock_backend.create_model.call_args[0][0]
        assert passed_config.id == "test"
        assert passed_config.provider == "openai"
        assert passed_config.temperature == 0.7


class TestModelBackendCreation:
    """Test backend-specific model creation to verify correct model identifier is used."""

    def test_strands_backend_uses_model_field_not_id(self):
        """Test that Strands backend uses model_config.model, not model_config.id."""
        from fivcplayground.backends.strands.models import (
            StrandsModelBackend,
        )

        model_config = ModelConfig(
            id="default",  # Config ID
            provider="openai",
            model="gpt-4o-mini",  # Actual model name
            api_key="sk-test",
        )

        with patch("fivcplayground.backends.strands.models.OpenAIModel") as mock_openai:
            backend = StrandsModelBackend()
            backend.create_model(model_config)

            # Verify that model_config.model (not model_config.id) was passed
            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args[1]
            assert call_kwargs["model_id"] == "gpt-4o-mini"
            assert call_kwargs["model_id"] != "default"

    def test_strands_backend_ollama_uses_model_field(self):
        """Test that Strands backend uses model_config.model for Ollama."""
        from fivcplayground.backends.strands.models import (
            StrandsModelBackend,
        )

        model_config = ModelConfig(
            id="ollama-config",
            provider="ollama",
            model="nomic-embed-text",
            base_url="http://localhost:11434",
        )

        with patch("fivcplayground.backends.strands.models.OllamaModel") as mock_ollama:
            backend = StrandsModelBackend()
            backend.create_model(model_config)

            # Verify that model_config.model (not model_config.id) was passed
            mock_ollama.assert_called_once()
            _ = mock_ollama.call_args[0]
            call_kwargs = mock_ollama.call_args[1]
            assert call_kwargs["model_id"] == "nomic-embed-text"
            assert call_kwargs["model_id"] != "ollama-config"

    def test_langchain_backend_uses_model_field_not_id(self):
        """Test that LangChain backend uses model_config.model, not model_config.id."""
        from fivcplayground.backends.langchain.models import (
            LangchainModelBackend,
        )

        model_config = ModelConfig(
            id="default",  # Config ID
            provider="openai",
            model="gpt-4o-mini",  # Actual model name
            api_key="sk-test",
        )

        with patch(
            "fivcplayground.backends.langchain.models.ChatOpenAI"
        ) as mock_openai:
            backend = LangchainModelBackend()
            backend.create_model(model_config)

            # Verify that model_config.model (not model_config.id) was passed
            mock_openai.assert_called_once()
            call_kwargs = mock_openai.call_args[1]
            assert call_kwargs["model"] == "gpt-4o-mini"
            assert call_kwargs["model"] != "default"

    def test_langchain_backend_ollama_uses_model_field(self):
        """Test that LangChain backend uses model_config.model for Ollama."""
        from fivcplayground.backends.langchain.models import (
            LangchainModelBackend,
        )

        model_config = ModelConfig(
            id="ollama-config",
            provider="ollama",
            model="llama2",
            base_url="http://localhost:11434",
        )

        with patch(
            "fivcplayground.backends.langchain.models.ChatOllama"
        ) as mock_ollama:
            backend = LangchainModelBackend()
            backend.create_model(model_config)

            # Verify that model_config.model (not model_config.id) was passed
            mock_ollama.assert_called_once()
            call_kwargs = mock_ollama.call_args[1]
            assert call_kwargs["model"] == "llama2"
            assert call_kwargs["model"] != "ollama-config"

    def test_model_config_id_vs_model_distinction(self):
        """Test that ModelConfig correctly distinguishes between id and model fields."""
        model_config = ModelConfig(
            id="my-gpt4-config",
            provider="openai",
            model="gpt-4",
            api_key="sk-test",
        )

        # Verify the distinction
        assert model_config.id == "my-gpt4-config"
        assert model_config.model == "gpt-4"
        assert model_config.id != model_config.model
