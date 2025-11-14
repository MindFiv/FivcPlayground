import os

from fivcglue.interfaces import (
    IComponentSite,
    configs,
)


class ConfigSession(configs.IConfigSession):
    """
    Configuration session that wraps a single configuration section.

    This class implements the IConfigSession interface from fivcglue,
    providing access to individual key-value pairs within a configuration section.
    """

    def __init__(self, session_name: str, session_data: dict):
        """
        Initialize a configuration session.

        Args:
            session_name: Name of the configuration session (e.g., "default_llm")
            session_data: Dictionary containing the configuration data for this session
        """
        self.session_name = session_name
        self.session_data = session_data or {}

    def list_keys(self) -> list[str]:
        """
        List all configuration keys available in this session.

        Returns all configuration key names present in the session, allowing
        you to discover what configuration values are available without
        needing to know the keys in advance.

        Returns:
            A list of all configuration key names in the session. Returns an
            empty list if the session contains no configuration keys.

        Example:
            >>> session = ConfigSession("default_llm", {"provider": "openai", "model": "gpt-4"})
            >>> keys = session.list_keys()
            >>> print(keys)
            ['provider', 'model']
            >>> for key in keys:
            ...     value = session.get_value(key)
            ...     print(f"{key}: {value}")
        """
        return list(self.session_data.keys())

    def get_value(self, key_name: str) -> str | None:
        """
        Get value by key from this configuration session.

        Args:
            key_name: The key to retrieve from the session data

        Returns:
            The value as a string if found, None otherwise.
            If the value is not a string, it will be converted to string.
        """
        value = self.session_data.get(key_name)
        if value is None:
            return None
        # Convert to string if not already
        if isinstance(value, str):
            return value
        return str(value)

    def set_value(self, key_name: str, value: str) -> bool:
        """Set a configuration value by key name.

        Args:
            key_name: The configuration key to set.
            value: The value to set.

        Returns:
            True if the value was set successfully, False otherwise.

        Example:
            >>> session = ConfigSession("default_llm", {"provider": "openai"})
            >>> session.set_value("model", "gpt-4")
            True
            >>> session.get_value("model")
            'gpt-4'
        """
        self.session_data[key_name] = value
        return True

    def delete_value(self, key_name: str) -> bool:
        """Delete a configuration value by key name.

        Args:
            key_name: The configuration key to delete.

        Returns:
            True if the value was deleted successfully, False if the key
            does not exist.

        Example:
            >>> session = ConfigSession("default_llm", {"provider": "openai", "model": "gpt-4"})
            >>> session.delete_value("model")
            True
            >>> session.get_value("model")
            None
            >>> session.delete_value("nonexistent")
            False
        """
        if key_name in self.session_data:
            del self.session_data[key_name]
            return True
        return False


class Config(configs.IConfig):
    """
    Settings configuration manager that implements the IConfig interface.

    This class loads configuration from YAML or JSON files and provides
    access to configuration data through the IConfig interface (get_session).
    """

    def __init__(
        self,
        component_site: IComponentSite,
        config_file: str = "settings.yaml",
    ):
        """
        Initialize the settings configuration.

        Args:
            component_site: An IComponentSite instance for component registration
            config_file: Config file path (defaults to "settings.yaml")
        """
        self.component_site = component_site
        self.config_file = os.path.abspath(os.path.join(os.getcwd(), config_file))
        self.errors = []
        self.configs = {}
        self.configs = self._load_file(self.config_file)
        if self.errors:
            print(f"Errors loading config: {self.errors}, in directory: {os.getcwd()}")

    def _load_yaml_file(self, filename: str):
        import yaml

        try:
            with open(filename, "r") as f:
                conf = yaml.safe_load(f)
                assert isinstance(conf, dict)
                return conf
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            yaml.YAMLError,
        ) as e:
            self.errors.append(e)
            return {}

    def _load_json_file(self, filename: str):
        import json

        try:
            with open(filename, "r") as f:
                conf = json.load(f)
                assert isinstance(conf, dict)
                return conf
        except (
            AssertionError,
            FileNotFoundError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as e:
            self.errors.append(e)
            return {}

    def _load_file(self, filename: str):
        ext = filename.split(".")[-1]
        if ext in ["yml", "yaml"]:
            return self._load_yaml_file(filename)
        elif ext == "json":
            return self._load_json_file(filename)
        else:
            self.errors.append(ValueError(f"Unsupported config file type: {ext}"))
            return {}

    def get_session(self, session_name: str) -> configs.IConfigSession | None:
        """
        Get a configuration session by name (IConfig interface method).

        This method implements the IConfig interface requirement. Each top-level
        configuration key is treated as a "session" that can be queried for
        individual values.

        Args:
            session_name: Name of the configuration session (e.g., "default_llm", "chat_llm")

        Returns:
            A ConfigSession instance if the session exists, None otherwise
        """
        session_data = self.configs.get(session_name)
        if session_data is None:
            return None

        # Ensure session_data is a dict (required for ConfigSession)
        if not isinstance(session_data, dict):
            # If it's not a dict, wrap it in a dict with a "value" key
            session_data = {"value": session_data}

        return ConfigSession(session_name, session_data)
