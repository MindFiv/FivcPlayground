"""
Settings provider interface for FivcPlayground.

This module defines the ISettingProvider interface for configuration management,
enabling flexible configuration source substitution (YAML, JSON, environment, database, etc.).
"""

from abc import abstractmethod
from typing import Iterable, Tuple, Any

from fivcglue.interfaces import IComponent


class ISetting(IComponent):
    """
    Interface for individual settings.

    This interface defines the contract for individual settings, which can be
    retrieved from a settings provider. It provides methods to get, set, and
    delete individual configuration values.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the setting."""

    @abstractmethod
    def get(self, key_name: str) -> str | None:
        """Get the value of the setting."""

    @abstractmethod
    def list(self) -> Iterable[Tuple[str, str]]:
        """List all key-value pairs in the setting."""


class ISettingProvider(IComponent):
    """
    Interface for settings providers.

    This interface defines the contract for settings providers, which manage
    and provide access to application settings. It provides methods to retrieve
    individual settings and list all available settings.
    """

    @abstractmethod
    def get_setting(
        self,
        name: str,
        user_id: str | None,
        **kwargs: Any,
    ) -> ISetting | None:
        """Get a setting by name."""

    @abstractmethod
    def list_settings(
        self,
        user_id: str | None,
        **kwargs: Any,
    ) -> Iterable[ISetting]:
        """List all settings."""
