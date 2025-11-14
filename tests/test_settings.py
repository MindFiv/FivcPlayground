#!/usr/bin/env python3
"""
Tests for the settings module.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock

from fivcplayground.settings.types import Config, ConfigSession
from fivcglue.interfaces import IComponentSite


@pytest.fixture
def mock_component_site():
    """Create a mock IComponentSite for testing."""
    site = Mock(spec=IComponentSite)
    return site


class TestConfig:
    """Test the Config class."""

    def test_init_nonexistent_file(self, mock_component_site):
        """Test initialization with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.yaml")
            config = Config(mock_component_site, config_path)

            assert config.configs == {}
            assert config.config_file == config_path
            assert len(config.errors) > 0

    def test_init_with_yaml_file(self, mock_component_site):
        """Test initialization with existing YAML file."""
        yaml_content = """
default_llm:
  provider: openai
  model: gpt-4
  temperature: 0.7
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = Config(mock_component_site, config_path)

            assert "default_llm" in config.configs
            assert config.configs["default_llm"]["provider"] == "openai"
            assert config.configs["default_llm"]["model"] == "gpt-4"
            assert config.configs["default_llm"]["temperature"] == 0.7
        finally:
            os.unlink(config_path)

    def test_init_with_json_file(self, mock_component_site):
        """Test initialization with existing JSON file."""
        json_content = """
{
  "default_llm": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7
  }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            f.flush()
            config_path = f.name

        try:
            config = Config(mock_component_site, config_path)

            assert "default_llm" in config.configs
            assert config.configs["default_llm"]["provider"] == "openai"
            assert config.configs["default_llm"]["model"] == "gpt-4"
            assert config.configs["default_llm"]["temperature"] == 0.7
        finally:
            os.unlink(config_path)

    def test_unsupported_file_type(self, mock_component_site):
        """Test initialization with unsupported file type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.txt")
            config = Config(mock_component_site, config_path)

            assert config.configs == {}
            assert len(config.errors) > 0

    def test_empty_yaml_file(self, mock_component_site):
        """Test handling of empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            config_path = f.name

        try:
            config = Config(mock_component_site, config_path)

            assert config.configs == {}
            assert len(config.errors) > 0
        finally:
            os.unlink(config_path)

    def test_invalid_yaml_file(self, mock_component_site):
        """Test handling of invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            config_path = f.name

        try:
            # Should handle invalid YAML gracefully
            config = Config(mock_component_site, config_path)
            # Depending on implementation, might be empty dict or raise exception
            assert isinstance(config.configs, dict)
            assert len(config.errors) > 0
        finally:
            os.unlink(config_path)

    def test_load_yaml_file_method(self, mock_component_site):
        """Test _load_yaml_file method."""
        yaml_content = """
test_key: test_value
number: 42
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = Config(mock_component_site, config_path)
            result = config._load_yaml_file(config_path)

            assert result["test_key"] == "test_value"
            assert result["number"] == 42
        finally:
            os.unlink(config_path)

    def test_load_json_file_method(self, mock_component_site):
        """Test _load_json_file method."""
        json_content = """
{
  "test_key": "test_value",
  "number": 42
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            f.flush()
            config_path = f.name

        try:
            config = Config(mock_component_site, config_path)
            result = config._load_json_file(config_path)

            assert result["test_key"] == "test_value"
            assert result["number"] == 42
        finally:
            os.unlink(config_path)

    def test_get_session_existing(self, mock_component_site):
        """Test get_session() returns IConfigSession for existing session."""
        yaml_content = """
default_llm:
  provider: openai
  model: gpt-4
  temperature: 0.7
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = Config(mock_component_site, config_path)
            session = config.get_session("default_llm")

            # Verify session is returned and implements IConfigSession
            assert session is not None
            assert isinstance(session, ConfigSession)
            assert hasattr(session, "get_value")

            # Verify session data
            assert session.session_name == "default_llm"
            assert session.get_value("provider") == "openai"
            assert session.get_value("model") == "gpt-4"
            assert session.get_value("temperature") == "0.7"
        finally:
            os.unlink(config_path)

    def test_get_session_nonexistent(self, mock_component_site):
        """Test get_session() returns None for non-existent session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = Config(mock_component_site, config_path)

            session = config.get_session("nonexistent")
            assert session is None

    def test_get_session_with_non_dict_value(self, mock_component_site):
        """Test get_session() handles non-dict values by wrapping them."""
        yaml_content = """
simple_value: just_a_string
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = Config(mock_component_site, config_path)
            session = config.get_session("simple_value")

            assert session is not None
            assert session.get_value("value") == "just_a_string"
        finally:
            os.unlink(config_path)

    def test_config_session_get_value(self):
        """Test ConfigSession.get_value() method."""
        session_data = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        session = ConfigSession("test_session", session_data)

        assert session.get_value("provider") == "openai"
        assert session.get_value("model") == "gpt-4"
        assert session.get_value("temperature") == "0.7"  # Converted to string
        assert session.get_value("max_tokens") == "1000"  # Converted to string
        assert session.get_value("nonexistent") is None

    def test_config_session_set_and_delete_value(self):
        """Test ConfigSession.set_value() and delete_value() methods."""
        session_data = {
            "provider": "openai",
            "model": "gpt-4",
        }
        session = ConfigSession("test_session", session_data)

        # Set a new value
        assert session.set_value("temperature", "0.7") is True
        assert session.get_value("temperature") == "0.7"
        assert "temperature" in session.list_keys()

        # Override existing value
        assert session.set_value("model", "gpt-4.1") is True
        assert session.get_value("model") == "gpt-4.1"

        # Delete existing key
        assert session.delete_value("provider") is True
        assert session.get_value("provider") is None
        assert "provider" not in session.list_keys()

        # Deleting non-existent key should return False
        assert session.delete_value("nonexistent") is False

    def test_config_session_list_keys(self):
        """Test ConfigSession.list_keys() method."""
        session_data = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        session = ConfigSession("test_session", session_data)

        keys = session.list_keys()

        # Verify all keys are returned
        assert isinstance(keys, list)
        assert len(keys) == 4
        assert "provider" in keys
        assert "model" in keys
        assert "temperature" in keys
        assert "max_tokens" in keys

    def test_config_session_list_keys_empty(self):
        """Test ConfigSession.list_keys() returns empty list for empty session."""
        session = ConfigSession("empty_session", {})

        keys = session.list_keys()

        assert isinstance(keys, list)
        assert len(keys) == 0

    def test_config_session_list_keys_with_none_data(self):
        """Test ConfigSession.list_keys() handles None session_data."""
        session = ConfigSession("none_session", None)

        keys = session.list_keys()

        assert isinstance(keys, list)
        assert len(keys) == 0

    def test_settings_config_implements_iconfig(self, mock_component_site):
        """Test that Config properly implements IConfig interface."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = Config(mock_component_site, config_path)

            # Verify required methods exist
            assert hasattr(config, "get_session")
            assert callable(config.get_session)


class TestSettingsModuleLazyValues:
    """Test lazy loading of settings module configurations."""

    def test_default_llm_args_lazy_loading(self):
        """Test that DEFAULT_LLM_ARGS is lazily loaded."""
        from fivcplayground import settings

        config = settings.DEFAULT_LLM_ARGS()
        assert isinstance(config, dict)
        assert "provider" in config

    def test_chat_llm_args_lazy_loading(self):
        """Test that CHAT_LLM_ARGS is lazily loaded."""
        from fivcplayground import settings

        config = settings.CHAT_LLM_ARGS()
        assert isinstance(config, dict)
        assert "provider" in config

    def test_reasoning_llm_args_lazy_loading(self):
        """Test that REASONING_LLM_ARGS is lazily loaded."""
        from fivcplayground import settings

        config = settings.REASONING_LLM_ARGS()
        assert isinstance(config, dict)
        assert "provider" in config

    def test_coding_llm_args_lazy_loading(self):
        """Test that CODING_LLM_ARGS is lazily loaded."""
        from fivcplayground import settings

        config = settings.CODING_LLM_ARGS()
        assert isinstance(config, dict)
        assert "provider" in config


if __name__ == "__main__":
    pytest.main([__file__])
