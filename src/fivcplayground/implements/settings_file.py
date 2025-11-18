"""
File-based implementation of settings interfaces.

This module provides file-based implementations of ISetting and ISettingProvider
interfaces, supporting YAML and JSON configuration files.

Classes:
    SettingImpl: Implementation of ISetting interface for individual settings
    SettingProviderImpl: Implementation of ISettingProvider interface for file-based settings
"""

import os
from typing import Iterable, Tuple, Any

from fivcglue.interfaces import IComponentSite

from fivcplayground.interfaces.settings import ISetting, ISettingProvider


class SettingImpl(ISetting):
    """
    Implementation of ISetting interface.

    This class represents a single setting (configuration section) loaded from a file.
    It provides access to key-value pairs within that setting.

    Example:
        >>> setting = SettingImpl("default_llm", {"provider": "openai", "model": "gpt-4"})
        >>> setting.get("provider")
        'openai'
        >>> list(setting.list())
        [('provider', 'openai'), ('model', 'gpt-4')]
    """

    def __init__(self, name: str, data: dict):
        """
        Initialize a file-based setting.

        Args:
            name: Name of the setting (e.g., "default_llm")
            data: Dictionary containing the setting's key-value pairs
        """
        self._name = name
        self.data = data or {}

    @property
    def name(self) -> str:
        """Get the name of the setting."""
        return self._name

    def get(self, key_name: str) -> str | None:
        """
        Get the value of a key in this setting.

        Args:
            key_name: The key to retrieve

        Returns:
            The value as a string if found, None otherwise.
            Non-string values are converted to strings.
        """
        value = self.data.get(key_name)
        if value is None:
            return None
        # Convert to string if not already
        if isinstance(value, str):
            return value
        return str(value)

    def list(self) -> Iterable[Tuple[str, str]]:
        """
        List all key-value pairs in this setting.

        Returns:
            An iterable of (key, value) tuples where values are strings.
        """
        for key, value in self.data.items():
            str_value = str(value) if not isinstance(value, str) else value
            yield key, str_value


class SettingProviderImpl(ISettingProvider):
    """
    File-based implementation of ISettingProvider interface.

    This class loads configuration from YAML or JSON files and provides
    access to settings through the ISettingProvider interface.

    Configuration is loaded lazily on first access to get_setting() or list_settings().

    Supported file formats:
    - YAML (.yaml, .yml)
    - JSON (.json)

    The configuration file is expected to have a hierarchical structure where
    top-level keys represent setting names, and their values are dictionaries
    of key-value pairs.

    Example:
        >>> provider = SettingProviderImpl(component_site, "settings.yaml")
        >>> setting = provider.get_setting("default_llm", user_id=None)
        >>> if setting:
        ...     model = setting.get("model")

    Configuration file example (settings.yaml):
        default_llm:
          provider: openai
          model: gpt-4
        chat_llm:
          provider: openai
          model: gpt-4-turbo
    """

    def __init__(
        self,
        component_site: IComponentSite,
        config_file: str = "settings.yaml",
        **kwargs: Any,
    ):
        """
        Initialize the file-based settings provider.

        Configuration is loaded lazily on first access.

        Args:
            component_site: An IComponentSite instance for component registration
            config_file: Path to the configuration file (defaults to "settings.yaml")
        """
        self.component_site = component_site
        self.config_file = os.path.abspath(os.path.join(os.getcwd(), config_file))
        self.settings_data = None  # None indicates not yet loaded
        self._loaded = False

    def _load_yaml_file(self, filename: str) -> dict:
        """
        Load configuration from a YAML file.

        Args:
            filename: Path to the YAML file

        Returns:
            Dictionary containing the configuration, or empty dict if loading fails
        """
        import yaml

        try:
            with open(filename, "r") as f:
                conf = yaml.safe_load(f)
                if conf is None:
                    return {}
                if not isinstance(conf, dict):
                    raise ValueError(f"Expected dict, got {type(conf).__name__}")
                return conf
        except (
            FileNotFoundError,
            ValueError,
            TypeError,
            yaml.YAMLError,
        ):
            return {}

    def _load_json_file(self, filename: str) -> dict:
        """
        Load configuration from a JSON file.

        Args:
            filename: Path to the JSON file

        Returns:
            Dictionary containing the configuration, or empty dict if loading fails
        """
        import json

        try:
            with open(filename, "r") as f:
                conf = json.load(f)
                if not isinstance(conf, dict):
                    raise ValueError(f"Expected dict, got {type(conf).__name__}")
                return conf
        except (
            FileNotFoundError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):
            return {}

    def _ensure_loaded(self) -> None:
        """
        Ensure configuration is loaded (lazy loading).

        Loads the configuration file on first access and caches the result.
        """
        if self._loaded:
            return

        ext = self.config_file.split(".")[-1].lower()
        if ext in ["yml", "yaml"]:
            self.settings_data = self._load_yaml_file(self.config_file)
        elif ext == "json":
            self.settings_data = self._load_json_file(self.config_file)
        else:
            self.settings_data = {}

        self._loaded = True

    def get_setting(
        self,
        name: str,
        user_id: str | None,
        **kwargs: Any,
    ) -> ISetting | None:
        """
        Get a setting by name.

        Triggers lazy loading of configuration on first call.

        Args:
            name: Name of the setting to retrieve
            user_id: Optional user ID for multi-user support (currently not used for file-based settings)
            **kwargs: Additional configuration parameters

        Returns:
            A SettingImpl instance if the setting exists, None otherwise
        """
        self._ensure_loaded()
        setting_data = self.settings_data.get(name)
        if setting_data is None:
            return None

        # Ensure setting_data is a dict
        if not isinstance(setting_data, dict):
            # If it's not a dict, wrap it in a dict with a "value" key
            setting_data = {"value": setting_data}

        return SettingImpl(name, setting_data)

    def list_settings(
        self,
        user_id: str | None,
        **kwargs: Any,
    ) -> Iterable[ISetting]:
        """
        List all available settings.

        Triggers lazy loading of configuration on first call.

        Args:
            user_id: Optional user ID for multi-user support (currently not used for file-based settings)
            **kwargs: Additional configuration parameters

        Returns:
            An iterable of ISetting instances for all settings in the configuration
        """
        self._ensure_loaded()
        for name in self.settings_data.keys():
            setting = self.get_setting(name, user_id)
            if setting is not None:
                yield setting
