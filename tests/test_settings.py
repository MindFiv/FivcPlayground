#!/usr/bin/env python3
"""
Tests for the settings module.
"""

import os
import tempfile
import pytest

from fivcplayground.settings.types import SettingsConfig


class TestSettingsConfig:
    """Test the SettingsConfig class."""

    def test_init_nonexistent_file(self):
        """Test initialization with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.yaml")
            config = SettingsConfig(config_path)

            assert config.configs == {}
            assert config.config_file == config_path
            assert len(config.errors) > 0

    def test_init_with_yaml_file(self):
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
            config = SettingsConfig(config_path)

            assert "default_llm" in config.configs
            assert config.configs["default_llm"]["provider"] == "openai"
            assert config.configs["default_llm"]["model"] == "gpt-4"
            assert config.configs["default_llm"]["temperature"] == 0.7
        finally:
            os.unlink(config_path)

    def test_get_existing_key(self):
        """Test getting an existing configuration key."""
        yaml_content = """
test_key: test_value
nested:
  key: nested_value
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = SettingsConfig(config_path)

            assert config.get("test_key") == "test_value"
            assert config.get("nested") == {"key": "nested_value"}
        finally:
            os.unlink(config_path)

    def test_get_nonexistent_key(self):
        """Test getting a non-existent key returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = SettingsConfig(config_path)

            assert config.get("nonexistent") is None

    def test_get_with_default(self):
        """Test getting a key with default value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = SettingsConfig(config_path)

            assert config.get("nonexistent", "default_value") == "default_value"

    def test_init_with_json_file(self):
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
            config = SettingsConfig(config_path)

            assert "default_llm" in config.configs
            assert config.configs["default_llm"]["provider"] == "openai"
            assert config.configs["default_llm"]["model"] == "gpt-4"
            assert config.configs["default_llm"]["temperature"] == 0.7
        finally:
            os.unlink(config_path)

    def test_unsupported_file_type(self):
        """Test initialization with unsupported file type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.txt")
            config = SettingsConfig(config_path)

            assert config.configs == {}
            assert len(config.errors) > 0

    def test_empty_yaml_file(self):
        """Test handling of empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            config_path = f.name

        try:
            config = SettingsConfig(config_path)

            assert config.configs == {}
            assert len(config.errors) > 0
        finally:
            os.unlink(config_path)

    def test_invalid_yaml_file(self):
        """Test handling of invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            config_path = f.name

        try:
            # Should handle invalid YAML gracefully
            config = SettingsConfig(config_path)
            # Depending on implementation, might be empty dict or raise exception
            assert isinstance(config.configs, dict)
            assert len(config.errors) > 0
        finally:
            os.unlink(config_path)

    def test_load_yaml_file_method(self):
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
            config = SettingsConfig(config_path)
            result = config._load_yaml_file(config_path)

            assert result["test_key"] == "test_value"
            assert result["number"] == 42
        finally:
            os.unlink(config_path)

    def test_load_json_file_method(self):
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
            config = SettingsConfig(config_path)
            result = config._load_json_file(config_path)

            assert result["test_key"] == "test_value"
            assert result["number"] == 42
        finally:
            os.unlink(config_path)


class TestSettingsModuleLazyValues:
    """Test lazy loading of settings module configurations."""

    def test_config_lazy_loading(self):
        """Test that config is lazily loaded."""
        from fivcplayground import settings

        # Accessing config should work
        config = settings.config()
        assert config is not None

    def test_default_llm_config_lazy_loading(self):
        """Test that default_llm_config is lazily loaded."""
        from fivcplayground import settings

        config = settings.default_llm_config()
        assert isinstance(config, dict)
        assert "provider" in config

    def test_chat_llm_config_lazy_loading(self):
        """Test that chat_llm_config is lazily loaded."""
        from fivcplayground import settings

        config = settings.chat_llm_config()
        assert isinstance(config, dict)
        assert "provider" in config

    def test_reasoning_llm_config_lazy_loading(self):
        """Test that reasoning_llm_config is lazily loaded."""
        from fivcplayground import settings

        config = settings.reasoning_llm_config()
        assert isinstance(config, dict)
        assert "provider" in config

    def test_coding_llm_config_lazy_loading(self):
        """Test that coding_llm_config is lazily loaded."""
        from fivcplayground import settings

        config = settings.coding_llm_config()
        assert isinstance(config, dict)
        assert "provider" in config


if __name__ == "__main__":
    pytest.main([__file__])
