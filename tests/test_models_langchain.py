"""
Tests for LangChain model implementations.

Tests the ModelImpl and ModelProviderImpl classes from
fivcplayground.implements.models_langchain module.
"""

from unittest.mock import MagicMock, patch

import pytest

from fivcglue.implements.utils import ComponentSite
from fivcplayground.implements.models_langchain import ModelImpl, ModelProviderImpl
from fivcplayground.interfaces import (
    IModel,
    IModelProvider,
    ISetting,
    ISettingProvider,
    ModelConfig,
)


@pytest.fixture
def mock_component_site():
    """Create a mock component site for testing."""
    return ComponentSite()


@pytest.fixture
def mock_setting_provider():
    """Create a mock setting provider for testing."""
    provider = MagicMock(spec=ISettingProvider)
    return provider


@pytest.fixture
def mock_setting():
    """Create a mock setting for testing."""
    setting = MagicMock(spec=ISetting)
    setting.name = "default_llm"
    setting.list.return_value = [
        ("provider", "openai"),
        ("model", "gpt-4o-mini"),
        ("temperature", "0.5"),
    ]
    return setting


class TestModelImpl:
    """Tests for ModelImpl class with lazy loading."""

    def test_init(self):
        """Test ModelImpl initialization with lazy loading."""
        model = ModelImpl("default_llm", provider="openai", model="gpt-4o-mini")

        assert model.name == "default_llm"
        assert model._underlying is None  # Not created yet
        assert model._config == {"provider": "openai", "model": "gpt-4o-mini"}

    def test_name_property(self):
        """Test name property."""
        model = ModelImpl("chat_llm", provider="openai", model="gpt-4o-mini")

        assert model.name == "chat_llm"

    def test_config_property(self):
        """Test config property returns ModelConfig."""
        model = ModelImpl(
            "default_llm",
            provider="openai",
            model="gpt-4o-mini",
            api_key="sk-test",
            temperature=0.7,
        )

        config = model.config
        assert isinstance(config, ModelConfig)
        assert config.provider == "openai"
        assert config.model == "gpt-4o-mini"
        assert config.api_key == "sk-test"
        assert config.temperature == 0.7

    def test_get_underlying_lazy_loading(self):
        """Test get_underlying creates model on first call."""
        model = ModelImpl("default_llm", provider="openai", model="gpt-4o-mini")

        with patch(
            "fivcplayground.implements.models_langchain._create_model"
        ) as mock_create:
            mock_underlying = MagicMock()
            mock_create.return_value = mock_underlying

            # First call should create the model
            result1 = model.get_underlying()
            assert result1 is mock_underlying
            assert mock_create.call_count == 1

            # Second call should return cached model
            result2 = model.get_underlying()
            assert result2 is mock_underlying
            assert mock_create.call_count == 1  # Still 1, not called again

    def test_get_underlying_caching(self):
        """Test that get_underlying caches the model."""
        model = ModelImpl("default_llm", provider="openai", model="gpt-4o-mini")

        with patch(
            "fivcplayground.implements.models_langchain._create_model"
        ) as mock_create:
            mock_underlying = MagicMock()
            mock_create.return_value = mock_underlying

            # Multiple calls should use cache
            result1 = model.get_underlying()
            result2 = model.get_underlying()
            result3 = model.get_underlying()

            assert result1 is result2 is result3
            assert mock_create.call_count == 1

    def test_implements_imodel(self):
        """Test that ModelImpl implements IModel interface."""
        model = ModelImpl("test", provider="openai", model="gpt-4o-mini")
        assert isinstance(model, IModel)


class TestModelProviderImpl:
    """Tests for ModelProviderImpl class."""

    def test_init(self, mock_component_site, mock_setting_provider):
        """Test ModelProviderImpl initialization."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )

        provider = ModelProviderImpl(mock_component_site)

        assert provider._component_site is mock_component_site
        assert provider._setting_provider is mock_setting_provider
        assert provider._models_cache == {}

    def test_implements_imodelprovider(
        self, mock_component_site, mock_setting_provider
    ):
        """Test that ModelProviderImpl implements IModelProvider interface."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )

        provider = ModelProviderImpl(mock_component_site)
        assert isinstance(provider, IModelProvider)

    def test_get_model_existing(
        self, mock_component_site, mock_setting_provider, mock_setting
    ):
        """Test getting an existing model with lazy loading."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )
        mock_setting_provider.get_setting.return_value = mock_setting

        provider = ModelProviderImpl(mock_component_site)
        model = provider.get_model("default_llm")

        assert model is not None
        assert model.name == "default_llm"
        # Model should not be created yet (lazy loading)
        assert model._underlying is None
        mock_setting_provider.get_setting.assert_called_once_with("default_llm", None)

        # Now test that get_underlying creates the model
        with patch(
            "fivcplayground.implements.models_langchain._create_model"
        ) as mock_create:
            mock_underlying = MagicMock()
            mock_create.return_value = mock_underlying

            result = model.get_underlying()
            assert result is mock_underlying

    def test_get_model_nonexistent(self, mock_component_site, mock_setting_provider):
        """Test getting a non-existent model returns None."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )
        mock_setting_provider.get_setting.return_value = None

        provider = ModelProviderImpl(mock_component_site)
        model = provider.get_model("nonexistent")

        assert model is None

    def test_get_model_caching(
        self, mock_component_site, mock_setting_provider, mock_setting
    ):
        """Test that ModelImpl instances are cached after first retrieval."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )
        mock_setting_provider.get_setting.return_value = mock_setting

        provider = ModelProviderImpl(mock_component_site)

        # First call
        model1 = provider.get_model("default_llm")
        # Second call
        model2 = provider.get_model("default_llm")

        # Should be the same cached ModelImpl instance
        assert model1 is model2
        # get_setting should only be called once (cached)
        assert mock_setting_provider.get_setting.call_count == 1

    def test_get_model_with_kwargs_override(
        self, mock_component_site, mock_setting_provider, mock_setting
    ):
        """Test that kwargs override setting values."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )
        mock_setting_provider.get_setting.return_value = mock_setting

        provider = ModelProviderImpl(mock_component_site)
        model = provider.get_model("default_llm", temperature="0.7")

        # Verify config has overridden temperature
        assert model._config["temperature"] == "0.7"
        assert model._config["provider"] == "openai"  # From setting
        assert model._config["model"] == "gpt-4o-mini"  # From setting

    def test_get_model_creation_error_value_error(
        self, mock_component_site, mock_setting_provider, mock_setting
    ):
        """Test that ValueError in configuration returns None gracefully."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )
        # Simulate ValueError in setting.list()
        mock_setting.list.side_effect = ValueError("Invalid setting")
        mock_setting_provider.get_setting.return_value = mock_setting

        provider = ModelProviderImpl(mock_component_site)
        model = provider.get_model("default_llm")

        assert model is None

    def test_get_model_creation_error_type_error(
        self, mock_component_site, mock_setting_provider, mock_setting
    ):
        """Test that TypeError in configuration returns None gracefully."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )
        # Simulate TypeError in setting.list()
        mock_setting.list.side_effect = TypeError("Invalid type")
        mock_setting_provider.get_setting.return_value = mock_setting

        provider = ModelProviderImpl(mock_component_site)
        model = provider.get_model("default_llm")

        assert model is None

    def test_get_model_creation_error_attribute_error(
        self, mock_component_site, mock_setting_provider, mock_setting
    ):
        """Test that AttributeError in configuration returns None gracefully."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )
        # Simulate AttributeError in setting.list()
        mock_setting.list.side_effect = AttributeError("Missing attribute")
        mock_setting_provider.get_setting.return_value = mock_setting

        provider = ModelProviderImpl(mock_component_site)
        model = provider.get_model("default_llm")

        assert model is None

    def test_list_models(self, mock_component_site, mock_setting_provider):
        """Test listing all available models."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )

        # Create multiple mock settings
        setting1 = MagicMock(spec=ISetting)
        setting1.name = "default_llm"
        setting1.list.return_value = [("provider", "openai"), ("model", "gpt-4o-mini")]

        setting2 = MagicMock(spec=ISetting)
        setting2.name = "chat_llm"
        setting2.list.return_value = [("provider", "openai"), ("model", "gpt-4o-mini")]

        mock_setting_provider.list_settings.return_value = [setting1, setting2]

        provider = ModelProviderImpl(mock_component_site)
        models = list(provider.list_models(user_id=None))

        assert len(models) == 2
        assert models[0].name == "default_llm"
        assert models[1].name == "chat_llm"
        # Models should not be created yet (lazy loading)
        assert models[0]._underlying is None
        assert models[1]._underlying is None

    def test_list_models_with_partial_failures(
        self, mock_component_site, mock_setting_provider
    ):
        """Test that list_models returns successfully configured models."""
        mock_component_site.register_component(
            ISettingProvider, mock_setting_provider, "models"
        )

        # Create mock settings - both should succeed in get_model
        # (errors during get_underlying are deferred due to lazy loading)
        setting1 = MagicMock(spec=ISetting)
        setting1.name = "default_llm"
        setting1.list.return_value = [("provider", "openai"), ("model", "gpt-4o-mini")]

        setting2 = MagicMock(spec=ISetting)
        setting2.name = "chat_llm"
        setting2.list.return_value = [("provider", "ollama"), ("model", "llama2")]

        mock_setting_provider.list_settings.return_value = [setting1, setting2]

        provider = ModelProviderImpl(mock_component_site)
        models = list(provider.list_models())

        # Both models should be returned with lazy loading
        assert len(models) == 2
        assert models[0].name == "default_llm"
        assert models[1].name == "chat_llm"
        # Models should not be created yet (lazy loading)
        assert models[0]._underlying is None
        assert models[1]._underlying is None
