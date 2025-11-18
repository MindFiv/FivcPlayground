"""
Tests for file-based settings implementation.

Tests the SettingImpl and SettingProviderImpl classes from
fivcplayground.implements.settings_file module.
"""

import json
import os
import tempfile

import pytest

from fivcglue.implements.utils import ComponentSite
from fivcplayground.implements import SettingImpl, SettingProviderImpl
from fivcplayground.interfaces import ISetting, ISettingProvider


@pytest.fixture
def mock_component_site():
    """Create a mock component site for testing."""
    return ComponentSite()


class TestSettingImpl:
    """Tests for SettingImpl class."""

    def test_init(self):
        """Test SettingImpl initialization."""
        data = {"provider": "openai", "model": "gpt-4"}
        setting = SettingImpl("default_llm", data)

        assert setting.name == "default_llm"
        assert setting.data == data

    def test_get_existing_key(self):
        """Test getting an existing key."""
        data = {"provider": "openai", "model": "gpt-4"}
        setting = SettingImpl("default_llm", data)

        assert setting.get("provider") == "openai"
        assert setting.get("model") == "gpt-4"

    def test_get_nonexistent_key(self):
        """Test getting a non-existent key returns None."""
        data = {"provider": "openai"}
        setting = SettingImpl("default_llm", data)

        assert setting.get("nonexistent") is None

    def test_get_converts_to_string(self):
        """Test that non-string values are converted to strings."""
        data = {"temperature": 0.7, "max_tokens": 100}
        setting = SettingImpl("default_llm", data)

        assert setting.get("temperature") == "0.7"
        assert setting.get("max_tokens") == "100"

    def test_list_returns_tuples(self):
        """Test that list() returns key-value tuples."""
        data = {"provider": "openai", "model": "gpt-4"}
        setting = SettingImpl("default_llm", data)

        items = list(setting.list())
        assert len(items) == 2
        assert ("provider", "openai") in items
        assert ("model", "gpt-4") in items

    def test_list_empty_setting(self):
        """Test list() on empty setting."""
        setting = SettingImpl("empty", {})
        items = list(setting.list())
        assert items == []

    def test_implements_isetting(self):
        """Test that SettingImpl implements ISetting interface."""
        setting = SettingImpl("test", {})
        assert isinstance(setting, ISetting)


class TestSettingProviderImpl:
    """Tests for SettingProviderImpl class."""

    def test_init_with_yaml_file(self, mock_component_site):
        """Test initialization with YAML file."""
        yaml_content = """
default_llm:
  provider: openai
  model: gpt-4
chat_llm:
  provider: openai
  model: gpt-4-turbo
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            provider = SettingProviderImpl(mock_component_site, config_path)
            assert provider.get_setting("default_llm", user_id=None) is not None
            assert provider.get_setting("chat_llm", user_id=None) is not None
        finally:
            os.unlink(config_path)

    def test_init_with_json_file(self, mock_component_site):
        """Test initialization with JSON file."""
        json_content = {
            "default_llm": {"provider": "openai", "model": "gpt-4"},
            "chat_llm": {"provider": "openai", "model": "gpt-4-turbo"},
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_content, f)
            f.flush()
            config_path = f.name

        try:
            provider = SettingProviderImpl(mock_component_site, config_path)
            assert provider.get_setting("default_llm", user_id=None) is not None
        finally:
            os.unlink(config_path)

    def test_init_with_nonexistent_file(self, mock_component_site):
        """Test initialization with non-existent file."""
        provider = SettingProviderImpl(
            mock_component_site, "/nonexistent/path/settings.yaml"
        )
        # Should initialize gracefully with empty settings on first access
        assert provider.get_setting("nonexistent", user_id=None) is None
        assert provider.settings_data == {}

    def test_init_with_unsupported_file_type(self, mock_component_site):
        """Test initialization with unsupported file type."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("some content")
            f.flush()
            config_path = f.name

        try:
            provider = SettingProviderImpl(mock_component_site, config_path)
            # Should initialize gracefully with empty settings for unsupported file type
            assert provider.get_setting("test", user_id=None) is None
            assert provider.settings_data == {}
        finally:
            os.unlink(config_path)

    def test_get_setting_existing(self, mock_component_site):
        """Test getting an existing setting."""
        yaml_content = """
default_llm:
  provider: openai
  model: gpt-4
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            provider = SettingProviderImpl(mock_component_site, config_path)
            setting = provider.get_setting("default_llm", user_id=None)

            assert setting is not None
            assert isinstance(setting, ISetting)
            assert setting.get("provider") == "openai"
            assert setting.get("model") == "gpt-4"
        finally:
            os.unlink(config_path)

    def test_get_setting_nonexistent(self, mock_component_site):
        """Test getting a non-existent setting."""
        yaml_content = "default_llm:\n  provider: openai\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            provider = SettingProviderImpl(mock_component_site, config_path)
            setting = provider.get_setting("nonexistent", user_id=None)
            assert setting is None
        finally:
            os.unlink(config_path)

    def test_list_settings(self, mock_component_site):
        """Test listing all settings."""
        yaml_content = """
default_llm:
  provider: openai
  model: gpt-4
chat_llm:
  provider: openai
  model: gpt-4-turbo
default_embedding:
  provider: openai
  model: text-embedding-3-small
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            provider = SettingProviderImpl(mock_component_site, config_path)
            settings = list(provider.list_settings(user_id=None))

            assert len(settings) == 3
            setting_names = [s.name for s in settings]
            assert "default_llm" in setting_names
            assert "chat_llm" in setting_names
            assert "default_embedding" in setting_names
        finally:
            os.unlink(config_path)

    def test_implements_isettingprovider(self, mock_component_site):
        """Test that SettingProviderImpl implements ISettingProvider."""
        provider = SettingProviderImpl(mock_component_site)
        assert isinstance(provider, ISettingProvider)

    def test_empty_yaml_file(self, mock_component_site):
        """Test with empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            config_path = f.name

        try:
            provider = SettingProviderImpl(mock_component_site, config_path)
            settings = list(provider.list_settings(user_id=None))
            assert settings == []
        finally:
            os.unlink(config_path)

    def test_invalid_yaml_file(self, mock_component_site):
        """Test with invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            config_path = f.name

        try:
            provider = SettingProviderImpl(mock_component_site, config_path)
            # Should initialize gracefully with empty settings for invalid YAML
            assert provider.get_setting("test", user_id=None) is None
            assert provider.settings_data == {}
        finally:
            os.unlink(config_path)
