"""
Tests for model creation functions in fivcplayground.models module.

Tests verify:
- create_model with various model config IDs
- create_chat_model, create_reasoning_model, create_coding_model
- Error handling for missing configs
- Model backend creation
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fivcplayground.models import (
    create_model_async,
)
from fivcplayground.models.types.base import ModelConfig


class TestCreateModel:
    """Test create_model_async function."""

    @pytest.mark.asyncio
    async def test_create_model_with_valid_config(self):
        """Test creating model with valid configuration."""
        mock_model = Mock()
        mock_model_config = ModelConfig(
            id="test-model",
            provider="openai",
            model="gpt-4o-mini",
        )
        mock_model_repo = Mock()
        mock_model_repo.get_model_config_async = AsyncMock(
            return_value=mock_model_config
        )

        mock_backend = Mock()
        mock_backend.create_model.return_value = mock_model

        result = await create_model_async(
            model_backend=mock_backend,
            model_config_repository=mock_model_repo,
            model_config_id="test-model",
        )

        assert result == mock_model
        mock_model_repo.get_model_config_async.assert_called_once_with("test-model")
        mock_backend.create_model.assert_called_once_with(mock_model_config)

    @pytest.mark.asyncio
    async def test_create_model_missing_config(self):
        """Test create_model_async raises error when config not found."""
        mock_model_repo = Mock()
        mock_model_repo.get_model_config_async = AsyncMock(return_value=None)

        mock_backend = Mock()

        with pytest.raises(ValueError, match="Default model not found"):
            await create_model_async(
                model_backend=mock_backend, model_config_repository=mock_model_repo
            )

    @pytest.mark.asyncio
    async def test_create_model_default_config_id(self):
        """Test create_model_async uses 'default' as default config ID."""
        mock_model = Mock()
        mock_model_config = ModelConfig(
            id="default",
            provider="openai",
            model="gpt-4o-mini",
        )
        mock_model_repo = Mock()
        mock_model_repo.get_model_config_async = AsyncMock(
            return_value=mock_model_config
        )

        mock_backend = Mock()
        mock_backend.create_model.return_value = mock_model

        await create_model_async(
            model_backend=mock_backend, model_config_repository=mock_model_repo
        )

        mock_model_repo.get_model_config_async.assert_called_once_with("default")

    @pytest.mark.asyncio
    async def test_create_model_passes_config_to_backend(self):
        """Test create_model_async passes config to backend create function."""
        mock_model = Mock()
        mock_model_config = ModelConfig(
            id="test",
            provider="openai",
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000,
        )
        mock_model_repo = Mock()
        mock_model_repo.get_model_config_async = AsyncMock(
            return_value=mock_model_config
        )

        mock_backend = Mock()
        mock_backend.create_model.return_value = mock_model

        await create_model_async(
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

    def test_strands_backend_openai_uses_max_completion_tokens(self):
        """Test that Strands backend sends OpenAI's current token limit field."""
        from fivcplayground.backends.strands.models import (
            StrandsModelBackend,
        )

        model_config = ModelConfig(
            id="default",
            provider="openai",
            model="gpt-5-mini",
            api_key="sk-test",
            max_tokens=1000,
        )

        with patch("fivcplayground.backends.strands.models.OpenAIModel") as mock_openai:
            backend = StrandsModelBackend()
            backend.create_model(model_config)

            call_kwargs = mock_openai.call_args[1]
            assert call_kwargs["params"]["max_completion_tokens"] == 1000
            assert "max_tokens" not in call_kwargs["params"]

    def test_strands_backend_openai_omits_unset_max_tokens(self):
        """Test that Strands backend does not send null token limits to OpenAI."""
        from fivcplayground.backends.strands.models import (
            StrandsModelBackend,
        )

        model_config = ModelConfig(
            id="default",
            provider="openai",
            model="gpt-5-mini",
            api_key="sk-test",
        )

        with patch("fivcplayground.backends.strands.models.OpenAIModel") as mock_openai:
            backend = StrandsModelBackend()
            backend.create_model(model_config)

            call_kwargs = mock_openai.call_args[1]
            assert "max_completion_tokens" not in call_kwargs["params"]
            assert "max_tokens" not in call_kwargs["params"]
            assert "extra_body" not in call_kwargs["params"]

    def test_strands_backend_openai_applies_enable_thinking(self):
        """Test that Strands OpenAI-compatible models receive thinking control."""
        from fivcplayground.backends.strands.models import (
            StrandsModelBackend,
        )

        model_config = ModelConfig(
            id="reasoning",
            provider="openai",
            model="qwen-flash",
            api_key="sk-test",
            enable_thinking=False,
        )

        with patch("fivcplayground.backends.strands.models.OpenAIModel") as mock_openai:
            backend = StrandsModelBackend()
            backend.create_model(model_config)

            call_kwargs = mock_openai.call_args[1]
            assert call_kwargs["params"]["extra_body"]["enable_thinking"] is False

    def test_strands_backend_gemini_applies_enable_thinking(self):
        """Test that Strands Gemini models receive native thinking config."""
        from google.genai.types import ThinkingConfig

        from fivcplayground.backends.strands.models import (
            StrandsModelBackend,
        )

        model_config = ModelConfig(
            id="gemini-reasoning",
            provider="gemini",
            model="gemini-2.5-flash",
            api_key="sk-test",
            enable_thinking=False,
        )

        with patch("fivcplayground.backends.strands.models.GeminiModel") as mock_gemini:
            backend = StrandsModelBackend()
            backend.create_model(model_config)

            call_kwargs = mock_gemini.call_args[1]
            thinking_config = call_kwargs["params"]["thinkingConfig"]
            assert isinstance(thinking_config, ThinkingConfig)
            assert thinking_config.include_thoughts is False

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

    def test_strands_backend_ollama_applies_enable_thinking(self):
        """Test that Strands Ollama models receive best-effort thinking control."""
        from fivcplayground.backends.strands.models import (
            StrandsModelBackend,
        )

        model_config = ModelConfig(
            id="ollama-reasoning",
            provider="ollama",
            model="qwen3",
            base_url="http://localhost:11434",
            enable_thinking=False,
        )

        with patch("fivcplayground.backends.strands.models.OllamaModel") as mock_ollama:
            backend = StrandsModelBackend()
            backend.create_model(model_config)

            call_kwargs = mock_ollama.call_args[1]
            assert call_kwargs["additional_args"]["think"] is False

    def test_adk_backend_openai_applies_enable_thinking(self):
        """Test that ADK OpenAI-compatible models receive thinking control."""
        from fivcplayground.backends.adk.models import AdkModelBackend

        model_config = ModelConfig(
            id="reasoning",
            provider="openai",
            model="qwen-flash",
            api_key="sk-test",
            enable_thinking=False,
        )

        with patch("fivcplayground.backends.adk.models.LiteLlm") as mock_litellm:
            backend = AdkModelBackend()
            backend.create_model(model_config)

            call_kwargs = mock_litellm.call_args[1]
            assert call_kwargs["extra_body"]["enable_thinking"] is False

    def test_adk_backend_ollama_applies_enable_thinking(self):
        """Test that ADK Ollama models receive best-effort thinking control."""
        from fivcplayground.backends.adk.models import AdkModelBackend

        model_config = ModelConfig(
            id="ollama-reasoning",
            provider="ollama",
            model="qwen3",
            base_url="http://localhost:11434",
            enable_thinking=False,
        )

        with patch("fivcplayground.backends.adk.models.LiteLlm") as mock_litellm:
            backend = AdkModelBackend()
            backend.create_model(model_config)

            call_kwargs = mock_litellm.call_args[1]
            assert call_kwargs["think"] is False

    def test_adk_backend_anthropic_omits_enable_thinking(self):
        """Test that ADK Anthropic models do not receive unsupported thinking kwargs."""
        from fivcplayground.backends.adk.models import AdkModelBackend

        model_config = ModelConfig(
            id="anthropic-reasoning",
            provider="anthropic",
            model="claude-sonnet-4",
            api_key="sk-test",
            enable_thinking=False,
        )

        with patch("fivcplayground.backends.adk.models.LiteLlm") as mock_litellm:
            backend = AdkModelBackend()
            backend.create_model(model_config)

            call_kwargs = mock_litellm.call_args[1]
            assert "enable_thinking" not in call_kwargs
            assert "extra_body" not in call_kwargs
            assert "think" not in call_kwargs

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
