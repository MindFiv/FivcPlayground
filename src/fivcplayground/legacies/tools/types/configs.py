import os
from typing import Optional, List, Dict

# from langchain_mcp_adapters.sessions import (
#     Connection,
#     StdioConnection,
#     SSEConnection,
# )


class ToolsConfigValue(dict):
    """
    Configuration value for a single MCP server.

    This class extends dict to provide additional validation and conversion
    methods for MCP server configurations. It supports two types of
    configurations:
    1. Command-based: Runs a local command with optional args and env vars
    2. URL-based: Connects to an SSE (Server-Sent Events) endpoint
    """

    def __init__(self, *args, **kwargs):
        """Initialize ToolsConfigValue, ensuring it's initialized with a dict.

        Raises:
            ValueError: If the value cannot be converted to a dict.
        """
        super().__init__(*args, **kwargs)
        self.validate(raise_exception=True)

    def validate(self, raise_exception: bool = False) -> bool:
        """Validate that the configuration has required fields.

        A valid configuration must have either:
        - 'command' key for stdio-based MCP servers
        - 'url' key for SSE-based MCP servers

        Returns:
            bool: True if configuration is valid, False otherwise.
        """
        if not isinstance(self, dict):
            if raise_exception:
                raise ValueError("ToolsConfigValue must be initialized with a dict")
            return False

        # Must have either 'command' or 'url'
        has_command = "command" in self
        has_url = "url" in self

        if not (has_command or has_url):
            if raise_exception:
                raise ValueError("ToolsConfigValue must have 'command' or 'url' key")
            return False

        # If command-based, validate command and optional args/env
        if has_command:
            command = self.get("command")
            if not isinstance(command, str) or not command:
                if raise_exception:
                    raise ValueError(
                        "ToolsConfigValue 'command' must be a non-empty string"
                    )
                return False

            args = self.get("args")
            if args is not None and not isinstance(args, list):
                if raise_exception:
                    raise ValueError("ToolsConfigValue 'args' must be a list")
                return False

            env = self.get("env")
            if env is not None and not isinstance(env, dict):
                if raise_exception:
                    raise ValueError("ToolsConfigValue 'env' must be a dict")
                return False

        # If URL-based, validate URL
        if has_url:
            url = self.get("url")
            if not isinstance(url, str) or not url:
                if raise_exception:
                    raise ValueError(
                        "ToolsConfigValue 'url' must be a non-empty string"
                    )
                return False

        # Validate optional bundle field
        bundle = self.get("bundle")
        if bundle is not None and not isinstance(bundle, str):
            if raise_exception:
                raise ValueError("ToolsConfigValue 'bundle' must be a string")
            return False

        return True

    @property
    def value(self) -> Optional[dict]:
        if not self.validate():
            return None

        if "command" in self:
            # Command-based configuration
            command = self["command"]
            args = self.get("args") or []
            env = self.get("env") or {}

            # Merge with environment variables
            env.update(os.environ)

            return dict(
                transport="stdio",
                command=command,
                args=args,
                env=env,
            )

        elif "url" in self:
            # URL-based configuration
            url = self["url"]
            return dict(
                transport="sse",
                url=url,
            )

        else:
            return None


class ToolsConfig(object):
    """Configuration loader for MCP (Model Context Protocol) servers.

    Loads and manages MCP server configurations from YAML or JSON files.
    Supports parsing server configurations and saving them back to disk.
    """

    def __init__(self, config_file: str = "mcp.yaml", load: bool = True):
        """Initialize ToolsConfig with a configuration file.

        Args:
            config_file: Path to the configuration file (YAML or JSON).
                        Defaults to "mcp.yaml" in the current working directory.
        """
        self._errors = []
        self._config_file = os.path.abspath(os.path.join(os.getcwd(), config_file))
        self._configs: Dict[str, ToolsConfigValue] = {}
        if load:
            self.load()

    def list(self) -> List[str]:
        return list(self._configs.keys())

    def get(self, name: str) -> Optional[ToolsConfigValue]:
        return self._configs.get(name)

    def set(self, name: str, config: ToolsConfigValue | dict) -> bool:
        if not isinstance(config, ToolsConfigValue):
            if not isinstance(config, dict):
                raise ValueError(
                    f"Config must be a dict or ToolsConfigValue, got {type(config).__name__}"
                )
            config = ToolsConfigValue(config)

        if not config.validate():
            return False

        self._configs[name] = config
        return True

    def remove(self, name: str):
        """Remove a server configuration by name.

        Args:
            name: Name of the server configuration to remove.
        """
        self._configs.pop(name, None)

    def get_errors(self):
        """Get list of errors encountered during configuration loading.

        Returns:
            List of exceptions that occurred during loading or parsing.
        """
        return self._errors

    def save(self, filename: Optional[str] = None) -> None:
        """Save the current configuration to a file.

        Args:
            filename: Path to save the configuration to. If None, saves to the
                     original config_file path. File extension determines format
                     (YAML for .yaml/.yml, JSON for .json).
        """
        if filename is None:
            filename = self._config_file
        self._save_file(filename)

    def load(self, filename: Optional[str] = None) -> None:
        if filename is None:
            filename = self._config_file

        # Clear configs but preserve any errors from _load_file
        self._errors.clear()
        self._configs.clear()
        configs = self._load_file(filename)
        if self._errors:
            print(f"Errors loading config: {self._errors}, in directory: {os.getcwd()}")
        else:
            for k, v in configs.items():
                try:
                    self.set(k, v)
                except ValueError as e:
                    self._errors.append(e)

    def _load_yaml_file(self, filename):
        """Load configuration from a YAML file.

        Args:
            filename: Path to the YAML file to load.

        Returns:
            Dictionary containing the parsed configuration, or empty dict on error.
        """
        import yaml

        try:
            with open(filename, "r") as f:
                conf = yaml.safe_load(f)
                if conf is None:
                    self._errors.append(
                        ValueError(f"Empty or invalid YAML file: {filename}")
                    )
                    return {}
                assert isinstance(conf, dict)
                return conf
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            yaml.YAMLError,
        ) as e:
            self._errors.append(e)
            return {}

    def _load_json_file(self, filename):
        """Load configuration from a JSON file.

        Args:
            filename: Path to the JSON file to load.

        Returns:
            Dictionary containing the parsed configuration, or empty dict on error.
        """
        import json

        try:
            with open(filename, "r") as f:
                conf = json.load(f)
                if conf is None:
                    self._errors.append(
                        ValueError(f"Empty or invalid JSON file: {filename}")
                    )
                    return {}
                assert isinstance(conf, dict)
                return conf
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as e:
            self._errors.append(e)
            return {}

    def _load_file(self, filename):
        """Load configuration from a file based on its extension.

        Determines the file format (YAML or JSON) based on the file extension
        and calls the appropriate load method.

        Args:
            filename: Path to the file to load. Extension determines format.

        Returns:
            Dictionary containing the parsed configuration, or empty dict on error.
        """
        ext = filename.split(".")[-1]
        if ext in ["yml", "yaml"]:
            return self._load_yaml_file(filename)
        elif ext == "json":
            return self._load_json_file(filename)
        else:
            self._errors.append(ValueError(f"Unsupported config file type: {ext}"))
            return {}

    def _save_yaml_file(self, filename: str):
        """Save configuration to a YAML file.

        Args:
            filename: Path to the YAML file to save to.
        """
        import yaml

        try:
            # Ensure parent directory exists
            import os

            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Convert ToolsConfigValue objects to regular dicts for YAML serialization
            configs_to_save = {
                k: dict(v) if isinstance(v, ToolsConfigValue) else v
                for k, v in self._configs.items()
            }
            with open(filename, "w") as f:
                yaml.safe_dump(configs_to_save, f)
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            yaml.YAMLError,
        ) as e:
            self._errors.append(e)

    def _save_json_file(self, filename: str):
        """Save configuration to a JSON file.

        Args:
            filename: Path to the JSON file to save to.
        """
        import json

        try:
            # Ensure parent directory exists
            import os

            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Convert ToolsConfigValue objects to regular dicts for JSON serialization
            with open(filename, "w") as f:
                json.dump(self._configs, f)
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as e:
            self._errors.append(e)

    def _save_file(self, filename: str):
        """Save configuration to a file based on its extension.

        Determines the file format (YAML or JSON) based on the file extension
        and calls the appropriate save method.

        Args:
            filename: Path to the file to save to. Extension determines format.
        """
        ext = filename.split(".")[-1]
        if ext in ["yml", "yaml"]:
            self._save_yaml_file(filename)
        elif ext == "json":
            self._save_json_file(filename)
        else:
            self._errors.append(ValueError(f"Unsupported config file type: {ext}"))
