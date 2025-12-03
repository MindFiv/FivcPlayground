"""
File-based model configuration repository implementation.

This module provides FileModelConfigRepository, a file-based implementation
of ModelConfigRepository that stores model configurations in a single
consolidated YAML file.

Storage Structure:
    /<output_dir>/configs/
    └── models.yaml    # All model configurations (mapping of model_id -> ModelConfig)

This structure allows for:
    - Simple file-based storage
    - Easy inspection of model data
    - Human-readable YAML format
    - Simple backup and version control
    - Atomic updates of all models

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
    ...     id="gpt-4",
    ...     model="gpt-4",
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

from pathlib import Path
from typing import Optional, List
import yaml

from fivcplayground.models.types.base import ModelConfig
from fivcplayground.models.types.repositories.base import ModelConfigRepository
from fivcplayground.utils import OutputDir


class FileModelConfigRepository(ModelConfigRepository):
    """
    File-based repository for model configurations.

    Stores all model configurations in a single consolidated YAML file.
    All operations are thread-safe for single-process usage.

    Storage structure:
        /<output_dir>/configs/
        └── models.yaml    # All model configurations (mapping of model_id -> ModelConfig)

    Attributes:
        output_dir: OutputDir instance for the repository base directory
        base_path: Path object pointing to the repository root
        models_file: Path to the models.yaml file

    Note:
        - The YAML file uses UTF-8 encoding
        - Corrupted YAML files are logged and skipped during reads
        - Delete operations are safe to call on non-existent items
        - All write operations create necessary directories automatically
        - Missing YAML file is handled gracefully on first read
    """

    def __init__(self, output_dir: Optional[OutputDir] = None):
        """
        Initialize the file-based repository.

        Args:
            output_dir: Optional OutputDir for the repository. If not provided,
                       defaults to OutputDir().subdir("models")

        Note:
            The base directory and configs subdirectory are created automatically
            if they don't exist.
        """
        self.output_dir = output_dir or OutputDir().subdir("configs")
        self.base_path = Path(str(self.output_dir))
        self.models_file = self.base_path / "models.yaml"

        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_models_file(self) -> Path:
        """
        Get the file path for the consolidated models YAML file.

        Returns:
            Path to models.yaml file
        """
        return self.models_file

    def _load_models_data(self) -> dict:
        """
        Load all models from the YAML file.

        Returns:
            Dictionary mapping model_id to model data. Returns empty dict if file
            doesn't exist or is corrupted.
        """
        models_file = self._get_models_file()

        if not models_file.exists():
            return {}

        try:
            with open(models_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except (yaml.YAMLError, ValueError) as e:
            print(f"Error loading models from {models_file.name}: {e}")
            return {}

    def _save_models_data(self, models_data: dict) -> None:
        """
        Save all models to the YAML file.

        Args:
            models_data: Dictionary mapping model_id to model data
        """
        models_file = self._get_models_file()

        with open(models_file, "w", encoding="utf-8") as f:
            yaml.dump(models_data, f, default_flow_style=False, allow_unicode=True)

    def update_model_config(self, model_config: ModelConfig) -> None:
        """
        Create or update a model configuration.

        Stores model configuration in the consolidated YAML file. The model_id
        is derived from the model_config.id field.

        Args:
            model_config: ModelConfig instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same model will overwrite the existing configuration.
        """
        model_id = model_config.id

        # Load existing models
        models_data = self._load_models_data()

        # Serialize model config to dict
        model_data = model_config.model_dump(mode="json")

        # Update the model in the data
        models_data[model_id] = model_data

        # Save all models back to file
        self._save_models_data(models_data)

    def get_model_config(self, model_id: str) -> ModelConfig | None:
        """
        Retrieve a model configuration by ID.

        Args:
            model_id: Unique identifier for the model

        Returns:
            ModelConfig instance if found, None if model doesn't exist
            or if the YAML file is corrupted
        """
        models_data = self._load_models_data()

        if model_id not in models_data:
            return None

        try:
            model_data = models_data[model_id]
            model_data["id"] = model_id
            return ModelConfig.model_validate(model_data)
        except ValueError as e:
            print(f"Error loading model {model_id}: {e}")
            return None

    def list_model_configs(self, **kwargs) -> List[ModelConfig]:
        """
        List all model configurations in the repository.

        Returns:
            List of ModelConfig instances sorted by model_id.
            Returns empty list if no models exist.
        """
        models_data = self._load_models_data()
        models = []

        # Sort by model_id for consistent ordering
        for model_id in sorted(models_data.keys()):
            try:
                model_data = models_data[model_id]
                model_data["id"] = model_id
                config = ModelConfig.model_validate(model_data)
                models.append(config)
            except ValueError as e:
                print(f"Error loading model {model_id}: {e}")

        return models

    def delete_model_config(self, model_id: str) -> None:
        """
        Delete a model configuration.

        Args:
            model_id: Unique identifier for the model to delete

        Note:
            This operation is safe to call on non-existent models.
        """
        models_data = self._load_models_data()

        if model_id in models_data:
            del models_data[model_id]
            self._save_models_data(models_data)
