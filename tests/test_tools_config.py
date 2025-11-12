#!/usr/bin/env python3
"""
Tests for the tools/types/configs module.
"""

import os
import tempfile
import pytest

from fivcplayground.tools.types.configs import ToolsConfig, ToolsConfigValue


class TestToolsConfig:
    """Test the ToolsConfig class."""

    def test_init_nonexistent_file(self):
        """Test initialization with non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "nonexistent.yaml")
            config = ToolsConfig(config_path)

            assert config._configs == {}
            assert len(config._errors) > 0

    def test_init_with_yaml_file(self):
        """Test initialization with existing YAML file."""
        yaml_content = """
test_server:
  command: python
  args:
    - test.py
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = ToolsConfig(config_path)

            assert "test_server" in config._configs
            assert isinstance(config._configs["test_server"], ToolsConfigValue)
        finally:
            os.unlink(config_path)

    def test_get_connection_from_config(self):
        """Test getting connection from configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = ToolsConfig(config_path)

            # Add a valid configuration
            config.set("test_server", {"command": "python", "args": ["test.py"]})

            # Should be able to get the config value
            config_value = config.get("test_server")
            assert config_value is not None

            # Should have a connection property
            connection = config_value.value
            assert connection is not None

    def test_load_yaml_file_method(self):
        """Test _load_yaml_file method."""
        yaml_content = """
test_server:
  command: python
  args:
    - test.py
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = ToolsConfig(config_path)
            result = config._load_yaml_file(config_path)

            assert "test_server" in result
            assert result["test_server"]["command"] == "python"
        finally:
            os.unlink(config_path)

    def test_load_json_file_method(self):
        """Test _load_json_file method."""
        json_content = """
{
  "test_server": {
    "command": "python",
    "args": ["test.py"]
  }
}
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            f.flush()
            config_path = f.name

        try:
            config = ToolsConfig(config_path)
            result = config._load_json_file(config_path)

            assert "test_server" in result
            assert result["test_server"]["command"] == "python"
        finally:
            os.unlink(config_path)

    def test_empty_yaml_file(self):
        """Test handling of empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            config_path = f.name

        try:
            config = ToolsConfig(config_path)

            assert config._configs == {}
            assert len(config._errors) > 0
        finally:
            os.unlink(config_path)

    def test_invalid_yaml_file(self):
        """Test handling of invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            config_path = f.name

        try:
            config = ToolsConfig(config_path)

            assert isinstance(config._configs, dict)
            assert len(config._errors) > 0
        finally:
            os.unlink(config_path)

    def test_unsupported_file_type(self):
        """Test initialization with unsupported file type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.txt")
            config = ToolsConfig(config_path)

            assert config._configs == {}
            assert len(config._errors) > 0

    def test_save_yaml_file(self):
        """Test saving configuration to YAML file."""
        yaml_content = """
test_server:
  command: python
  args:
    - test.py
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial config file
            config_path = os.path.join(tmpdir, "test.yaml")
            with open(config_path, "w") as f:
                f.write(yaml_content)

            # Load and save
            config = ToolsConfig(config_path)
            save_path = os.path.join(tmpdir, "saved.yaml")
            config.save(save_path)

            # Verify saved file exists and contains data
            assert os.path.exists(save_path)
            with open(save_path, "r") as f:
                content = f.read()
                assert "test_server" in content or "python" in content

    def test_save_json_file(self):
        """Test saving configuration to JSON file."""
        json_content = """
{
  "test_server": {
    "command": "python",
    "args": ["test.py"]
  }
}
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial config file
            config_path = os.path.join(tmpdir, "test.json")
            with open(config_path, "w") as f:
                f.write(json_content)

            # Load and save
            config = ToolsConfig(config_path)
            save_path = os.path.join(tmpdir, "saved.json")
            config.save(save_path)

            # Verify saved file exists and contains data
            assert os.path.exists(save_path)
            with open(save_path, "r") as f:
                content = f.read()
                assert "test_server" in content or "python" in content

    def test_save_without_filename(self):
        """Test saving to default config file path."""
        yaml_content = """
test_server:
  command: python
  args:
    - test.py
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            with open(config_path, "w") as f:
                f.write(yaml_content)

            config = ToolsConfig(config_path)
            # Save without specifying filename (should use config_path)
            config.save()

            # Verify file was saved
            assert os.path.exists(config_path)

    def test_save_unsupported_file_type(self):
        """Test saving to unsupported file type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            with open(config_path, "w") as f:
                f.write("test: value")

            config = ToolsConfig(config_path)
            save_path = os.path.join(tmpdir, "test.txt")
            config.save(save_path)

            # Should have error for unsupported type
            assert len(config._errors) > 0

    def test_save_yaml_file_method(self):
        """Test _save_yaml_file method directly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            with open(config_path, "w") as f:
                f.write("test_server:\n  command: python\n  args:\n    - test.py")

            config = ToolsConfig(config_path)
            save_path = os.path.join(tmpdir, "saved.yaml")
            config._save_yaml_file(save_path)

            assert os.path.exists(save_path)

    def test_save_json_file_method(self):
        """Test _save_json_file method directly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.json")
            with open(config_path, "w") as f:
                f.write('{"test_server": {"command": "python", "args": ["test.py"]}}')

            config = ToolsConfig(config_path)
            save_path = os.path.join(tmpdir, "saved.json")
            config._save_json_file(save_path)

            assert os.path.exists(save_path)

    def test_save_file_method_yaml(self):
        """Test _save_file method with YAML extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            with open(config_path, "w") as f:
                f.write("test: value")

            config = ToolsConfig(config_path)
            save_path = os.path.join(tmpdir, "saved.yml")
            config._save_file(save_path)

            assert os.path.exists(save_path)

    def test_save_file_method_json(self):
        """Test _save_file method with JSON extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.json")
            with open(config_path, "w") as f:
                f.write('{"test": "value"}')

            config = ToolsConfig(config_path)
            save_path = os.path.join(tmpdir, "saved.json")
            config._save_file(save_path)

            assert os.path.exists(save_path)


class TestToolsConfigValue:
    """Test the ToolsConfigValue class."""

    def test_validate_command_based_config(self):
        """Test validation of command-based configuration."""
        config = ToolsConfigValue({"command": "python", "args": ["test.py"]})
        assert config.validate() is True

    def test_validate_command_based_config_minimal(self):
        """Test validation of minimal command-based configuration."""
        config = ToolsConfigValue({"command": "python"})
        assert config.validate() is True

    def test_validate_command_based_config_with_env(self):
        """Test validation of command-based configuration with env vars."""
        config = ToolsConfigValue(
            {"command": "python", "args": ["test.py"], "env": {"VAR": "value"}}
        )
        assert config.validate() is True

    def test_validate_url_based_config(self):
        """Test validation of URL-based configuration."""
        config = ToolsConfigValue({"url": "http://localhost:8000"})
        assert config.validate() is True

    def test_validate_invalid_no_command_or_url(self):
        """Test validation fails when neither command nor url is provided."""
        with pytest.raises(ValueError, match="must have 'command' or 'url' key"):
            ToolsConfigValue({"args": ["test.py"]})

    def test_validate_invalid_empty_command(self):
        """Test validation fails with empty command."""
        with pytest.raises(ValueError, match="'command' must be a non-empty string"):
            ToolsConfigValue({"command": ""})

    def test_validate_invalid_command_not_string(self):
        """Test validation fails when command is not a string."""
        with pytest.raises(ValueError, match="'command' must be a non-empty string"):
            ToolsConfigValue({"command": 123})

    def test_validate_invalid_args_not_list(self):
        """Test validation fails when args is not a list."""
        with pytest.raises(ValueError, match="'args' must be a list"):
            ToolsConfigValue({"command": "python", "args": "test.py"})

    def test_validate_invalid_env_not_dict(self):
        """Test validation fails when env is not a dict."""
        with pytest.raises(ValueError, match="'env' must be a dict"):
            ToolsConfigValue({"command": "python", "env": "VAR=value"})

    def test_validate_invalid_empty_url(self):
        """Test validation fails with empty URL."""
        with pytest.raises(ValueError, match="'url' must be a non-empty string"):
            ToolsConfigValue({"url": ""})

    def test_validate_invalid_url_not_string(self):
        """Test validation fails when URL is not a string."""
        with pytest.raises(ValueError, match="'url' must be a non-empty string"):
            ToolsConfigValue({"url": 123})

    def test_connection_command_based(self):
        """Test connection property returns StdioConnection for command-based config."""
        config = ToolsConfigValue({"command": "python", "args": ["test.py"]})
        connection = config.value
        assert connection is not None
        assert isinstance(connection, dict)
        assert connection.get("transport") == "stdio"
        assert connection.get("command") == "python"
        assert connection.get("args") == ["test.py"]

    def test_connection_url_based(self):
        """Test connection property returns SSEConnection for URL-based config."""
        config = ToolsConfigValue({"url": "http://localhost:8000"})
        connection = config.value
        assert connection is not None
        assert isinstance(connection, dict)
        assert connection.get("transport") == "sse"
        assert connection.get("url") == "http://localhost:8000"

    def test_connection_with_env_vars(self):
        """Test connection property includes environment variables."""
        config = ToolsConfigValue(
            {
                "command": "python",
                "args": ["test.py"],
                "env": {"CUSTOM_VAR": "custom_value"},
            }
        )
        connection = config.value
        assert connection is not None
        assert isinstance(connection, dict)
        assert "CUSTOM_VAR" in connection.get("env", {})


class TestToolsConfigSet:
    """Test the set method of ToolsConfig class."""

    def test_set_with_dict(self):
        """Test set method with dict argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = ToolsConfig(config_path)

            result = config.set(
                "new_server", {"command": "python", "args": ["test.py"]}
            )
            assert result is True
            assert "new_server" in config._configs
            assert isinstance(config._configs["new_server"], ToolsConfigValue)

    def test_set_with_toolsconfigvalue(self):
        """Test set method with ToolsConfigValue argument."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = ToolsConfig(config_path)

            cfg = ToolsConfigValue({"url": "http://localhost:8000"})
            result = config.set("new_server", cfg)
            assert result is True
            assert "new_server" in config._configs

    def test_set_with_invalid_config(self):
        """Test set method with invalid configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = ToolsConfig(config_path)

            # Invalid config should raise ValueError
            with pytest.raises(ValueError):
                config.set("invalid_server", {"args": ["test.py"]})


class TestToolsConfigLoad:
    """Test the load method of ToolsConfig class."""

    def test_load_yaml_file(self):
        """Test loading YAML configuration file."""
        yaml_content = """
test_server:
  command: python
  args:
    - test.py
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = ToolsConfig(config_path)
            # Verify initial load
            assert "test_server" in config._configs

            # Create a new file and load it
            yaml_content2 = """
another_server:
  url: http://localhost:8000
"""
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as f2:
                f2.write(yaml_content2)
                f2.flush()
                config_path2 = f2.name

            try:
                config.load(config_path2)
                assert "another_server" in config._configs
                assert "test_server" not in config._configs
            finally:
                os.unlink(config_path2)
        finally:
            os.unlink(config_path)

    def test_load_without_filename(self):
        """Test load method without filename uses config_file."""
        yaml_content = """
test_server:
  command: python
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            config_path = f.name

        try:
            config = ToolsConfig(config_path)
            initial_configs = dict(config._configs)

            # Load without filename should reload from config_file
            config.load()
            assert config._configs == initial_configs
        finally:
            os.unlink(config_path)


class TestToolsConfigSerialization:
    """Test serialization of ToolsConfig and ToolsConfigValue to YAML and JSON."""

    def test_yaml_dump_toolsconfigvalue_requires_conversion(self):
        """Test that ToolsConfigValue must be converted to dict before YAML dump."""
        import yaml

        config = ToolsConfigValue({"command": "python", "args": ["test.py"]})

        # Direct dump should raise RepresenterError
        with pytest.raises(yaml.representer.RepresenterError):
            yaml.safe_dump({"test_server": config})

        # But converting to dict first should work
        yaml_str = yaml.safe_dump({"test_server": dict(config)})
        assert "command: python" in yaml_str
        assert "test.py" in yaml_str

    def test_json_dump_toolsconfigvalue_works(self):
        """Test that ToolsConfigValue can be dumped to JSON (dict subclass is JSON serializable)."""
        import json

        config = ToolsConfigValue({"command": "python", "args": ["test.py"]})

        # JSON can serialize dict subclasses directly
        json_str = json.dumps({"test_server": config})
        assert "command" in json_str
        assert "python" in json_str

        # Converting to dict also works
        json_str2 = json.dumps({"test_server": dict(config)})
        assert "command" in json_str2
        assert "python" in json_str2

    def test_yaml_dump_mixed_configs_requires_conversion(self):
        """Test dumping mixed ToolsConfigValue and regular dict configs requires conversion."""
        import yaml

        configs = {
            "mcp_server": ToolsConfigValue({"command": "python"}),
            "regular_config": {"key": "value"},
        }

        # Direct dump should raise RepresenterError
        with pytest.raises(yaml.representer.RepresenterError):
            yaml.safe_dump(configs)

        # But converting ToolsConfigValue to dict first should work
        converted_configs = {
            k: dict(v) if isinstance(v, ToolsConfigValue) else v
            for k, v in configs.items()
        }
        yaml_str = yaml.safe_dump(converted_configs)
        assert "command: python" in yaml_str
        assert "key: value" in yaml_str

    def test_json_dump_mixed_configs_works(self):
        """Test dumping mixed ToolsConfigValue and regular dict configs to JSON."""
        import json

        configs = {
            "mcp_server": ToolsConfigValue({"command": "python"}),
            "regular_config": {"key": "value"},
        }

        # JSON can serialize dict subclasses directly
        json_str = json.dumps(configs)
        assert "command" in json_str
        assert "key" in json_str

        # Converting ToolsConfigValue to dict also works
        converted_configs = {
            k: dict(v) if isinstance(v, ToolsConfigValue) else v
            for k, v in configs.items()
        }
        json_str2 = json.dumps(converted_configs)
        assert "command" in json_str2
        assert "key" in json_str2

    def test_toolsconfig_save_yaml_with_toolsconfigvalue(self):
        """Test that ToolsConfig.save() works with ToolsConfigValue objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.yaml")
            config = ToolsConfig(config_path)

            # Add a valid MCP config (will be stored as ToolsConfigValue)
            config.set("test_server", {"command": "python", "args": ["test.py"]})

            # Save should not raise RepresenterError
            save_path = os.path.join(tmpdir, "saved.yaml")
            config.save(save_path)

            # Verify file was created and contains the config
            assert os.path.exists(save_path)
            with open(save_path, "r") as f:
                content = f.read()
                assert "command: python" in content

    def test_toolsconfig_save_json_with_toolsconfigvalue(self):
        """Test that ToolsConfig.save() works with ToolsConfigValue objects to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test.json")
            config = ToolsConfig(config_path)

            # Add a valid MCP config (will be stored as ToolsConfigValue)
            config.set("test_server", {"command": "python", "args": ["test.py"]})

            # Save should not raise TypeError
            save_path = os.path.join(tmpdir, "saved.json")
            config.save(save_path)

            # Verify file was created and contains the config
            assert os.path.exists(save_path)
            with open(save_path, "r") as f:
                content = f.read()
                assert "command" in content
                assert "python" in content

    def test_toolsconfig_roundtrip_yaml_with_toolsconfigvalue(self):
        """Test loading and saving ToolsConfigValue objects to YAML."""
        yaml_content = """
test_server:
  command: python
  args:
    - test.py
another_server:
  url: http://localhost:8000
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial config file
            config_path = os.path.join(tmpdir, "test.yaml")
            with open(config_path, "w") as f:
                f.write(yaml_content)

            # Load config
            config = ToolsConfig(config_path)
            assert "test_server" in config._configs
            assert "another_server" in config._configs

            # Save to new file
            save_path = os.path.join(tmpdir, "saved.yaml")
            config.save(save_path)

            # Load the saved file and verify
            config2 = ToolsConfig(save_path)
            assert "test_server" in config2._configs
            assert "another_server" in config2._configs

    def test_toolsconfig_roundtrip_json_with_toolsconfigvalue(self):
        """Test loading and saving ToolsConfigValue objects to JSON."""
        json_content = """{
  "test_server": {
    "command": "python",
    "args": ["test.py"]
  },
  "another_server": {
    "url": "http://localhost:8000"
  }
}"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial config file
            config_path = os.path.join(tmpdir, "test.json")
            with open(config_path, "w") as f:
                f.write(json_content)

            # Load config
            config = ToolsConfig(config_path)
            assert "test_server" in config._configs
            assert "another_server" in config._configs

            # Save to new file
            save_path = os.path.join(tmpdir, "saved.json")
            config.save(save_path)

            # Load the saved file and verify
            config2 = ToolsConfig(save_path)
            assert "test_server" in config2._configs
            assert "another_server" in config2._configs

    def test_dict_conversion_preserves_data(self):
        """Test that converting ToolsConfigValue to dict preserves all data."""
        original_data = {
            "command": "python",
            "args": ["test.py", "arg1"],
            "env": {"VAR": "value"},
        }
        config = ToolsConfigValue(original_data)

        # Convert to dict
        converted = dict(config)

        # Verify all data is preserved
        assert converted == original_data
        assert converted["command"] == "python"
        assert converted["args"] == ["test.py", "arg1"]
        assert converted["env"] == {"VAR": "value"}

    def test_yaml_dump_nested_toolsconfigvalue_requires_conversion(self):
        """Test dumping nested structures with ToolsConfigValue requires conversion."""
        import yaml

        configs = {
            "mcpServers": {
                "playwright": ToolsConfigValue(
                    {"command": "npx", "args": ["@playwright/mcp@latest"]}
                ),
                "other": ToolsConfigValue({"url": "http://localhost:8000"}),
            }
        }

        # Direct dump should raise RepresenterError
        with pytest.raises(yaml.representer.RepresenterError):
            yaml.safe_dump(configs)

        # But converting nested ToolsConfigValue to dict should work
        converted_configs = {
            "mcpServers": {
                k: dict(v) if isinstance(v, ToolsConfigValue) else v
                for k, v in configs["mcpServers"].items()
            }
        }
        yaml_str = yaml.safe_dump(converted_configs)
        assert "playwright:" in yaml_str
        assert "command: npx" in yaml_str
        assert "other:" in yaml_str
        assert "url: http://localhost:8000" in yaml_str


if __name__ == "__main__":
    pytest.main([__file__])
