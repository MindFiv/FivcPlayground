"""
File-based model configuration repository implementation.

This module provides FileModelConfigRepository, a file-based implementation
of ModelConfigRepository that stores model configurations in a hierarchical
directory structure with JSON files.

Storage Structure:
    /<output_dir>/
    └── model_<model_id>.json    # Model configuration (ModelConfig)

This structure allows for:
    - Simple file-based storage
    - Easy inspection of model data
    - Human-readable JSON format
    - Simple backup and version control

Example:
    >>> from fivcplayground.models.types.repositories.files import FileModelConfigRepository
    >>> from fivcplayground.models.types.base import ModelConfig
    >>> from fivcplayground.utils import OutputDir
    >>>
    >>> # Create repository
    >>> repo = FileModelConfigRepository(output_dir=OutputDir("./models"))
    >>>
    >>> # Store model configuration
    >>> model_config = ModelConfig(
    ...     name="gpt-4",
    ...     provider="openai",
    ...     api_key="sk-...",
    ...     temperature=0.7
    ... )
    >>> repo.update_model_config(model_config)
    >>>
    >>> # Retrieve model configuration
    >>> config = repo.get_model_config("gpt-4")
    >>>
    >>> # List all models
    >>> models = repo.list_model_configs()
"""

import json
from pathlib import Path
from typing import Optional, List, Any

from fivcplayground.models.types.base import ModelConfig
from fivcplayground.models.types.repositories.base import ModelConfigRepository
from fivcplayground.utils import OutputDir


class FileModelConfigRepository(ModelConfigRepository):
    """
    File-based repository for model configurations.

    Stores model configurations in JSON files within a directory structure.
    All operations are thread-safe for single-process usage.

    Storage structure:
        /<output_dir>/
        └── model_<model_id>.json    # Model configuration

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
                       defaults to OutputDir().subdir("models")

        Note:
            The base directory is created automatically if it doesn't exist.
        """
        self.output_dir = output_dir or OutputDir().subdir("models")
        self.base_path = Path(str(self.output_dir))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_model_file(self, model_id: str) -> Path:
        """
        Get the file path for a model configuration.

        Args:
            model_id: Model identifier

        Returns:
            Path to model configuration file (e.g., /<base_path>/model_<model_id>.json)
        """
        return self.base_path / f"model_{model_id}.json"

    def update_model_config(self, model_config: ModelConfig) -> None:
        """
        Create or update a model configuration.

        Stores model configuration in a JSON file. The model_id is derived from
        the model_config.id field.

        Args:
            model_config: ModelConfig instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same model will overwrite the existing configuration.
        """
        model_id = model_config.id
        model_file = self._get_model_file(model_id)

        # Serialize model config to JSON
        model_data = model_config.model_dump(mode="json")

        with open(model_file, "w", encoding="utf-8") as f:
            json.dump(model_data, f, indent=2, ensure_ascii=False)

    def get_model_config(self, model_id: str) -> ModelConfig | None:
        """
        Retrieve a model configuration by ID.

        Args:
            model_id: Unique identifier for the model

        Returns:
            ModelConfig instance if found, None if model doesn't exist
            or if the JSON file is corrupted
        """
        model_file = self._get_model_file(model_id)

        if not model_file.exists():
            return None

        try:
            with open(model_file, "r", encoding="utf-8") as f:
                model_data = json.load(f)

            return ModelConfig.model_validate(model_data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading model {model_id}: {e}")
            return None

    def list_model_configs(self, **kwargs) -> List[ModelConfig]:
        """
        List all model configurations in the repository.

        Returns:
            List of ModelConfig instances sorted by model_id.
            Returns empty list if no models exist.
        """
        models = []

        if not self.base_path.exists():
            return models

        for model_file in sorted(self.base_path.glob("model_*.json")):
            try:
                with open(model_file, "r", encoding="utf-8") as f:
                    model_data = json.load(f)
                config = ModelConfig.model_validate(model_data)
                models.append(config)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading model from {model_file.name}: {e}")

        return models

    def delete_model_config(self, model_id: str) -> None:
        """
        Delete a model configuration.

        Args:
            model_id: Unique identifier for the model to delete

        Note:
            This operation is safe to call on non-existent models.
        """
        model_file = self._get_model_file(model_id)
        if model_file.exists():
            model_file.unlink()

    def filter_repository(
        self,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> "FileModelConfigRepository":
        """Filter the repository.

        Args:
            user_id: Optional user ID to filter by
            kwargs: Additional keyword arguments for filtering

        Returns:
            Filtered repository
        """
        return self
