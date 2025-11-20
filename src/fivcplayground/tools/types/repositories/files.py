"""
File-based tool configuration repository implementation.

This module provides FileToolConfigRepository, a file-based implementation
of ToolConfigRepository that stores tool configurations in a hierarchical
directory structure with JSON files.

Storage Structure:
    /<output_dir>/
    └── tool_<tool_id>.json    # Tool configuration (ToolConfig)

This structure allows for:
    - Simple file-based storage
    - Easy inspection of tool data
    - Human-readable JSON format
    - Simple backup and version control

Example:
    >>> from fivcplayground.tools.types.repositories.files import FileToolConfigRepository
    >>> from fivcplayground.tools.types.base import ToolConfig
    >>> from fivcplayground.utils import OutputDir
    >>>
    >>> # Create repository
    >>> repo = FileToolConfigRepository(output_dir=OutputDir("./tools"))
    >>>
    >>> # Store tool configuration
    >>> tool_config = ToolConfig(
    ...     id="calculator",
    ...     description="A calculator tool",
    ...     transport="stdio",
    ...     command="python",
    ...     args=["calculator.py"]
    ... )
    >>> repo.update_tool_config(tool_config)
    >>>
    >>> # Retrieve tool configuration
    >>> config = repo.get_tool_config("calculator")
    >>>
    >>> # List all tools
    >>> tools = repo.list_tool_configs()
"""

import json
from pathlib import Path
from typing import Optional, List, Any

from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.tools.types.repositories.base import ToolConfigRepository
from fivcplayground.utils import OutputDir


class FileToolConfigRepository(ToolConfigRepository):
    """
    File-based repository for tool configurations.

    Stores tool configurations in JSON files within a directory structure.
    All operations are thread-safe for single-process usage.

    Storage structure:
        /<output_dir>/
        └── tool_<tool_id>.json    # Tool configuration

    Attributes:
        output_dir: OutputDir instance for the repository base directory
        base_path: Path object pointing to the repository root

    Note:
        - All JSON files use UTF-8 encoding with 2-space indentation
        - Corrupted JSON files are logged and skipped during reads
        - Delete operations are safe to call on non-existent items
        - All write operations create necessary directories automatically
    """

    def __init__(self, output_dir: Optional[OutputDir] = None):
        """
        Initialize the file-based repository.

        Args:
            output_dir: Optional OutputDir for the repository. If not provided,
                       defaults to OutputDir().subdir("tools")

        Note:
            The base directory is created automatically if it doesn't exist.
        """
        self.output_dir = output_dir or OutputDir().subdir("tools")
        self.base_path = Path(str(self.output_dir))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_tool_file(self, tool_id: str) -> Path:
        """
        Get the file path for a tool configuration.

        Args:
            tool_id: Tool identifier

        Returns:
            Path to tool configuration file (e.g., /<base_path>/tool_<tool_id>.json)
        """
        return self.base_path / f"tool_{tool_id}.json"

    def update_tool_config(self, tool_config: ToolConfig) -> None:
        """
        Create or update a tool configuration.

        Stores tool configuration in a JSON file. The tool_id is derived from
        the tool_config.id field.

        Args:
            tool_config: ToolConfig instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same tool will overwrite the existing configuration.
        """
        tool_id = tool_config.id
        tool_file = self._get_tool_file(tool_id)

        # Serialize tool config to JSON
        tool_data = tool_config.model_dump(mode="json")

        with open(tool_file, "w", encoding="utf-8") as f:
            json.dump(tool_data, f, indent=2, ensure_ascii=False)

    def get_tool_config(self, tool_id: str) -> ToolConfig | None:
        """
        Retrieve a tool configuration by ID.

        Args:
            tool_id: Unique identifier for the tool

        Returns:
            ToolConfig instance if found, None if tool doesn't exist
            or if the JSON file is corrupted
        """
        tool_file = self._get_tool_file(tool_id)

        if not tool_file.exists():
            return None

        try:
            with open(tool_file, "r", encoding="utf-8") as f:
                tool_data = json.load(f)

            return ToolConfig.model_validate(tool_data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading tool {tool_id}: {e}")
            return None

    def list_tool_configs(self, **kwargs) -> List[ToolConfig]:
        """
        List all tool configurations in the repository.

        Returns:
            List of ToolConfig instances sorted by tool_id.
            Returns empty list if no tools exist.
        """
        tools = []

        if not self.base_path.exists():
            return tools

        for tool_file in sorted(self.base_path.glob("tool_*.json")):
            try:
                with open(tool_file, "r", encoding="utf-8") as f:
                    tool_data = json.load(f)
                config = ToolConfig.model_validate(tool_data)
                tools.append(config)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading tool from {tool_file.name}: {e}")

        return tools

    def delete_tool_config(self, tool_id: str) -> None:
        """
        Delete a tool configuration.

        Args:
            tool_id: Unique identifier for the tool to delete

        Note:
            This operation is safe to call on non-existent tools.
        """
        tool_file = self._get_tool_file(tool_id)
        if tool_file.exists():
            tool_file.unlink()

    def filter_repository(
        self,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> "FileToolConfigRepository":
        """Filter the repository.

        Args:
            user_id: Optional user ID to filter by
            kwargs: Additional keyword arguments for filtering

        Returns:
            Filtered repository
        """
        return self
