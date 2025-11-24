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
    create_chat_model,
    create_reasoning_model,
    create_coding_model,
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

        with patch("fivcplayground.models._create_model") as mock_backend_create:
            mock_backend_create.return_value = mock_model

            result = create_model(
                model_config_repository=mock_model_repo,
                model_config_id="test-model",
            )

            assert result == mock_model
            mock_model_repo.get_model_config.assert_called_once_with("test-model")
            mock_backend_create.assert_called_once_with(mock_model_config)

    def test_create_model_missing_config(self):
        """Test create_model raises error when config not found."""
        mock_model_repo = Mock()
        mock_model_repo.get_model_config.return_value = None

        with pytest.raises(ValueError, match="Default model not found"):
            create_model(model_config_repository=mock_model_repo)

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

        with patch(
            "fivcplayground.models.types.backends.create_model"
        ) as mock_backend_create:
            mock_backend_create.return_value = mock_model

            create_model(model_config_repository=mock_model_repo)

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

        with patch("fivcplayground.models._create_model") as mock_backend_create:
            mock_backend_create.return_value = mock_model

            create_model(model_config_repository=mock_model_repo)

            # Verify the config was passed to backend
            mock_backend_create.assert_called_once()
            passed_config = mock_backend_create.call_args[0][0]
            assert passed_config.id == "test"
            assert passed_config.provider == "openai"
            assert passed_config.temperature == 0.7


class TestSpecializedModelCreation:
    """Test specialized model creation functions."""

    def _setup_mocks(self, model_id):
        """Helper to setup mocks for model creation."""
        mock_model = Mock()
        mock_model_config = ModelConfig(
            id=model_id,
            provider="openai",
            model="gpt-4o-mini",
        )
        mock_model_repo = Mock()
        mock_model_repo.get_model_config.return_value = mock_model_config
        return mock_model, mock_model_repo

    def test_create_chat_model(self):
        """Test create_chat_model."""
        mock_model, mock_model_repo = self._setup_mocks("chat")

        with patch("fivcplayground.models._create_model") as mock_backend_create:
            mock_backend_create.return_value = mock_model

            result = create_chat_model(model_config_repository=mock_model_repo)

            assert result == mock_model
            mock_model_repo.get_model_config.assert_called_once_with("chat")

    def test_create_reasoning_model(self):
        """Test create_reasoning_model."""
        mock_model, mock_model_repo = self._setup_mocks("reasoning")

        with patch("fivcplayground.models._create_model") as mock_backend_create:
            mock_backend_create.return_value = mock_model

            result = create_reasoning_model(model_config_repository=mock_model_repo)

            assert result == mock_model
            mock_model_repo.get_model_config.assert_called_once_with("reasoning")

    def test_create_coding_model(self):
        """Test create_coding_model."""
        mock_model, mock_model_repo = self._setup_mocks("coding")

        with patch("fivcplayground.models._create_model") as mock_backend_create:
            mock_backend_create.return_value = mock_model

            result = create_coding_model(model_config_repository=mock_model_repo)

            assert result == mock_model
            mock_model_repo.get_model_config.assert_called_once_with("coding")
