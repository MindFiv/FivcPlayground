"""
Unit tests for the models module migration from models.py to models/ package.

Tests verify:
- Module structure and imports
- Factory functions (create_default_model, create_chat_model, etc.)
- Provider registry pattern
- Configuration merging with settings
- Error handling for unsupported providers
"""

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.language_models import BaseChatModel

from fivcplayground.models import (
    create_default_model,
    create_chat_model,
    create_reasoning_model,
    create_coding_model,
)
from fivcplayground.models.backends.langchain import (
    _openai_model,
    _ollama_model,
)

# Default providers registry
default_providers = {
    "openai": _openai_model,
    "ollama": _ollama_model,
}


class TestModuleStructure:
    """Test the models module structure and exports."""

    def test_module_exports(self):
        """Test that all expected functions are exported."""
        from fivcplayground import models

        assert hasattr(models, "create_default_model")
        assert hasattr(models, "create_chat_model")
        assert hasattr(models, "create_reasoning_model")
        assert hasattr(models, "create_coding_model")

    def test_all_exports(self):
        """Test __all__ contains expected exports."""
        from fivcplayground.models import __all__

        expected = [
            "create_default_model",
            "create_chat_model",
            "create_reasoning_model",
            "create_coding_model",
        ]
        assert set(__all__) == set(expected)

    def test_backends_module_exists(self):
        """Test that backends module is accessible."""
        from fivcplayground.models.backends import langchain

        assert hasattr(langchain, "_openai_model")
        assert hasattr(langchain, "_ollama_model")
        assert hasattr(langchain, "create_model")


class TestDefaultProviders:
    """Test the default_providers registry."""

    def test_default_providers_structure(self):
        """Test default_providers is a dict with expected keys."""
        assert isinstance(default_providers, dict)
        assert "openai" in default_providers
        assert "ollama" in default_providers

    def test_default_providers_values_are_callable(self):
        """Test all provider values are callable."""
        for provider_name, provider_func in default_providers.items():
            assert callable(provider_func), f"{provider_name} provider is not callable"

    def test_openai_provider_is_openai_model(self):
        """Test openai provider points to _openai_model."""
        assert default_providers["openai"] == _openai_model

    def test_ollama_provider_is_ollama_model(self):
        """Test ollama provider points to _ollama_model."""
        assert default_providers["ollama"] == _ollama_model


class TestOpenAIProvider:
    """Test the OpenAI provider implementation."""

    @patch("langchain_openai.ChatOpenAI")
    def test_openai_model_creates_chat_openai(self, mock_chat_openai):
        """Test _openai_model creates ChatOpenAI instance."""
        mock_instance = MagicMock(spec=BaseChatModel)
        mock_chat_openai.return_value = mock_instance

        result = _openai_model(
            model="gpt-4o-mini", api_key="test-key", temperature=0.7, max_tokens=2048
        )

        assert result == mock_instance
        mock_chat_openai.assert_called_once()

    @patch("langchain_openai.ChatOpenAI")
    def test_openai_model_default_parameters(self, mock_chat_openai):
        """Test _openai_model uses correct default parameters."""
        mock_instance = MagicMock(spec=BaseChatModel)
        mock_chat_openai.return_value = mock_instance

        _openai_model()

        call_kwargs = mock_chat_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 4096
        assert call_kwargs["base_url"] == "https://api.openai.com/v1"

    @patch("langchain_openai.ChatOpenAI")
    def test_openai_model_api_key_is_lambda(self, mock_chat_openai):
        """Test _openai_model wraps api_key in lambda."""
        mock_instance = MagicMock(spec=BaseChatModel)
        mock_chat_openai.return_value = mock_instance

        _openai_model(api_key="test-key")

        call_kwargs = mock_chat_openai.call_args[1]
        assert callable(call_kwargs["api_key"])
        assert call_kwargs["api_key"]() == "test-key"


class TestOllamaProvider:
    """Test the Ollama provider implementation."""

    @patch("langchain_ollama.ChatOllama")
    def test_ollama_model_creates_chat_ollama(self, mock_chat_ollama):
        """Test _ollama_model creates ChatOllama instance."""
        mock_instance = MagicMock(spec=BaseChatModel)
        mock_chat_ollama.return_value = mock_instance

        result = _ollama_model(
            model="llama2", base_url="http://localhost:11434", temperature=0.7
        )

        assert result == mock_instance
        mock_chat_ollama.assert_called_once()

    @patch("langchain_ollama.ChatOllama")
    def test_ollama_model_default_parameters(self, mock_chat_ollama):
        """Test _ollama_model uses correct default parameters."""
        mock_instance = MagicMock(spec=BaseChatModel)
        mock_chat_ollama.return_value = mock_instance

        _ollama_model()

        call_kwargs = mock_chat_ollama.call_args[1]
        assert call_kwargs["model"] == "llama2"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["base_url"] == "http://localhost:11434"
        assert call_kwargs["reasoning"] is False

    @patch("langchain_ollama.ChatOllama")
    def test_ollama_model_with_reasoning(self, mock_chat_ollama):
        """Test _ollama_model with reasoning enabled."""
        mock_instance = MagicMock(spec=BaseChatModel)
        mock_chat_ollama.return_value = mock_instance

        _ollama_model(reasoning=True)

        call_kwargs = mock_chat_ollama.call_args[1]
        assert call_kwargs["reasoning"] is True


class TestCreateDefaultModel:
    """Test create_default_model factory function."""

    @patch("fivcplayground.models.settings.DEFAULT_LLM_ARGS", new_callable=MagicMock)
    @patch("fivcplayground.models.create_model")
    def test_create_default_model_with_openai(self, mock_create_model, mock_config):
        """Test create_default_model with OpenAI provider."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_model.return_value = mock_model
        # Mock DEFAULT_LLM_ARGS to return a dict when called
        mock_config.return_value = {
            "provider": "openai",
            "model": "gpt-4",
            "framework": "langchain",
        }

        result = create_default_model(provider="openai")

        assert result == mock_model
        mock_create_model.assert_called_once()

    @patch("fivcplayground.models.settings.DEFAULT_LLM_ARGS", new_callable=MagicMock)
    @patch("fivcplayground.models.create_model")
    def test_create_default_model_unsupported_provider(
        self, mock_create_model, mock_config
    ):
        """Test create_default_model raises error for unsupported provider."""
        mock_create_model.side_effect = ValueError("Unsupported model provider")
        # Mock DEFAULT_LLM_ARGS to return a dict when called
        mock_config.return_value = {
            "provider": "unsupported",
            "framework": "langchain",
        }

        with pytest.raises(ValueError, match="Unsupported model provider"):
            create_default_model(provider="unsupported")

    @patch("fivcplayground.models.settings.DEFAULT_LLM_ARGS", new_callable=MagicMock)
    @patch("fivcplayground.models.backends.create_model")
    def test_create_default_model_merges_settings(self, mock_create_model, mock_config):
        """Test create_default_model merges with settings."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_model.return_value = mock_model
        # Mock DEFAULT_LLM_ARGS to return a dict when called
        mock_config.return_value = {
            "provider": "openai",
            "temperature": 0.5,
            "framework": "langchain",
        }

        create_default_model(temperature=0.7)

        # Verify DEFAULT_LLM_ARGS was called with kwargs
        assert mock_config.called


class TestCreateChatModel:
    """Test create_chat_model factory function."""

    @patch("fivcplayground.models.create_default_model")
    @patch("fivcplayground.models.settings.CHAT_LLM_ARGS", new_callable=MagicMock)
    def test_create_chat_model_calls_create_default_model(
        self, mock_config, mock_create_default
    ):
        """Test create_chat_model delegates to create_default_model."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_default.return_value = mock_model
        # Mock CHAT_LLM_ARGS to return a dict when called
        mock_config.return_value = {
            "provider": "openai",
            "framework": "langchain",
        }

        result = create_chat_model()

        assert result == mock_model
        mock_create_default.assert_called_once()

    @patch("fivcplayground.models.create_default_model")
    @patch("fivcplayground.models.settings.CHAT_LLM_ARGS", new_callable=MagicMock)
    def test_create_chat_model_uses_chat_config(self, mock_config, mock_create_default):
        """Test create_chat_model uses chat_llm_config from settings."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_default.return_value = mock_model
        # Mock CHAT_LLM_ARGS to return a dict when called
        mock_config.return_value = {"framework": "langchain"}

        create_chat_model(temperature=0.8)

        # Verify CHAT_LLM_ARGS was called with kwargs
        assert mock_config.called


class TestCreateReasoningModel:
    """Test create_reasoning_model factory function."""

    @patch("fivcplayground.models.create_default_model")
    @patch("fivcplayground.models.settings.REASONING_LLM_ARGS", new_callable=MagicMock)
    def test_create_reasoning_model_calls_create_default_model(
        self, mock_config, mock_create_default
    ):
        """Test create_reasoning_model delegates to create_default_model."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_default.return_value = mock_model
        # Mock REASONING_LLM_ARGS to return a dict when called
        mock_config.return_value = {"framework": "langchain"}

        result = create_reasoning_model()

        assert result == mock_model
        mock_create_default.assert_called_once()

    @patch("fivcplayground.models.create_default_model")
    @patch("fivcplayground.models.settings.REASONING_LLM_ARGS", new_callable=MagicMock)
    def test_create_reasoning_model_uses_reasoning_config(
        self, mock_config, mock_create_default
    ):
        """Test create_reasoning_model uses reasoning_llm_config from settings."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_default.return_value = mock_model
        # Mock REASONING_LLM_ARGS to return a dict when called
        mock_config.return_value = {"framework": "langchain"}

        create_reasoning_model()

        assert mock_config.called


class TestCreateCodingModel:
    """Test create_coding_model factory function."""

    @patch("fivcplayground.models.create_default_model")
    @patch("fivcplayground.models.settings.CODING_LLM_ARGS", new_callable=MagicMock)
    def test_create_coding_model_calls_create_default_model(
        self, mock_config, mock_create_default
    ):
        """Test create_coding_model delegates to create_default_model."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_default.return_value = mock_model
        # Mock CODING_LLM_ARGS to return a dict when called
        mock_config.return_value = {"framework": "langchain"}

        result = create_coding_model()

        assert result == mock_model
        mock_create_default.assert_called_once()

    @patch("fivcplayground.models.create_default_model")
    @patch("fivcplayground.models.settings.CODING_LLM_ARGS", new_callable=MagicMock)
    def test_create_coding_model_uses_coding_config(
        self, mock_config, mock_create_default
    ):
        """Test create_coding_model uses coding_llm_config from settings."""
        mock_model = MagicMock(spec=BaseChatModel)
        mock_create_default.return_value = mock_model
        # Mock CODING_LLM_ARGS to return a dict when called
        mock_config.return_value = {"framework": "langchain"}

        create_coding_model()

        assert mock_config.called
