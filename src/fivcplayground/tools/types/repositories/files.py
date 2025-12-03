"""
File-based tool configuration repository implementation.

This module provides FileToolConfigRepository, a file-based implementation
of ToolConfigRepository that stores tool configurations in a single
consolidated YAML file.

Storage Structure:
    /<output_dir>/configs/
    └── tools.yaml    # All tool configurations (mapping of tool_id -> ToolConfig)

This structure allows for:
    - Simple file-based storage
    - Easy inspection of tool data
    - Human-readable YAML format
    - Simple backup and version control
    - Atomic updates of all tools

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

import yaml
from pathlib import Path
from typing import Optional, List

from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.tools.types.repositories.base import ToolConfigRepository
from fivcplayground.utils import OutputDir


class FileToolConfigRepository(ToolConfigRepository):
    """
    File-based repository for tool configurations.

    Stores all tool configurations in a single consolidated YAML file.
    All operations are thread-safe for single-process usage.

    Storage structure:
        /<output_dir>/configs/
        └── tools.yaml    # All tool configurations (mapping of tool_id -> ToolConfig)

    Attributes:
        output_dir: OutputDir instance for the repository base directory
        base_path: Path object pointing to the repository root
        tools_file: Path to the tools.yaml file

    Note:
        - YAML file uses UTF-8 encoding
        - Corrupted YAML files are logged and skipped during reads
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
            The base directory and configs directory are created automatically if they don't exist.
        """
        self.output_dir = output_dir or OutputDir().subdir("configs")
        self.base_path = Path(str(self.output_dir))
        self.tools_file = self.base_path / "tools.yaml"
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_tools_file(self) -> Path:
        """
        Get the file path for the consolidated tools YAML file.

        Returns:
            Path to tools.yaml file
        """
        return self.tools_file

    def _load_tools_data(self) -> dict:
        """
        Load all tools from the YAML file.

        Returns:
            Dictionary mapping tool_id to tool data. Returns empty dict if file
            doesn't exist or is corrupted.
        """
        tools_file = self._get_tools_file()

        if not tools_file.exists():
            return {}

        try:
            with open(tools_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except (yaml.YAMLError, ValueError) as e:
            print(f"Error loading tools from {tools_file.name}: {e}")
            return {}

    def _save_tools_data(self, tools_data: dict) -> None:
        """
        Save all tools to the YAML file.

        Args:
            tools_data: Dictionary mapping tool_id to tool data
        """
        tools_file = self._get_tools_file()
        with open(tools_file, "w", encoding="utf-8") as f:
            yaml.dump(tools_data, f, default_flow_style=False, allow_unicode=True)

    def update_tool_config(self, tool_config: ToolConfig) -> None:
        """
        Create or update a tool configuration.

        Stores tool configuration in the consolidated YAML file. The tool_id is derived from
        the tool_config.id field.

        Args:
            tool_config: ToolConfig instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same tool will overwrite the existing configuration.
        """
        tool_id = tool_config.id

        # Load existing tools
        tools_data = self._load_tools_data()

        # Serialize tool config to dict
        tool_data = tool_config.model_dump(mode="json")

        # Update the tool in the data
        tools_data[tool_id] = tool_data

        # Save all tools back to file
        self._save_tools_data(tools_data)

    def get_tool_config(self, tool_id: str) -> ToolConfig | None:
        """
        Retrieve a tool configuration by ID.

        Args:
            tool_id: Unique identifier for the tool

        Returns:
            ToolConfig instance if found, None if tool doesn't exist
            or if the YAML file is corrupted
        """
        tools_data = self._load_tools_data()

        if tool_id not in tools_data:
            return None

        try:
            tool_data = tools_data[tool_id]
            tool_data["id"] = tool_id
            return ToolConfig.model_validate(tool_data)
        except ValueError as e:
            print(f"Error loading tool {tool_id}: {e}")
            return None

    def list_tool_configs(self, **kwargs) -> List[ToolConfig]:
        """
        List all tool configurations in the repository.

        Returns:
            List of ToolConfig instances sorted by tool_id.
            Returns empty list if no tools exist.
        """
        tools_data = self._load_tools_data()
        tools = []

        # Sort by tool_id for consistent ordering
        for tool_id in sorted(tools_data.keys()):
            try:
                tool_data = tools_data[tool_id]
                tool_data["id"] = tool_id
                config = ToolConfig.model_validate(tool_data)
                tools.append(config)
            except ValueError as e:
                print(f"Error loading tool {tool_id}: {e}")

        return tools

    def delete_tool_config(self, tool_id: str) -> None:
        """
        Delete a tool configuration.

        Args:
            tool_id: Unique identifier for the tool to delete

        Note:
            This operation is safe to call on non-existent tools.
        """
        tools_data = self._load_tools_data()

        if tool_id in tools_data:
            del tools_data[tool_id]
            self._save_tools_data(tools_data)
