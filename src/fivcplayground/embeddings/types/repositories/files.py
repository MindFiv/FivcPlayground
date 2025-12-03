"""
File-based embedding configuration repository implementation.

This module provides FileEmbeddingConfigRepository, a file-based implementation
of EmbeddingConfigRepository that stores embedding configurations in a single
consolidated YAML file.

Storage Structure:
    /<output_dir>/configs/
    └── embeddings.yaml    # All embedding configurations (mapping of embedding_id -> EmbeddingConfig)

This structure allows for:
    - Simple file-based storage
    - Easy inspection of embedding data
    - Human-readable YAML format
    - Simple backup and version control
    - Atomic updates of all embeddings

Example:
    >>> from fivcplayground.embeddings.types.repositories.files import FileEmbeddingConfigRepository
    >>> from fivcplayground.embeddings.types.base import EmbeddingConfig
    >>> from fivcplayground.utils import OutputDir
    >>>
    >>> # Create repository
    >>> repo = FileEmbeddingConfigRepository(output_dir=OutputDir("./embeddings"))
    >>>
    >>> # Store embedding configuration
    >>> embedding_config = EmbeddingConfig(
    ...     id="openai-ada",
    ...     provider="openai",
    ...     model="text-embedding-ada-002",
    ...     api_key="sk-...",
    ...     dimension=1536
    ... )
    >>> repo.update_embedding_config(embedding_config)
    >>>
    >>> # Retrieve embedding configuration
    >>> config = repo.get_embedding_config("openai-ada")
    >>>
    >>> # List all embeddings
    >>> embeddings = repo.list_embedding_configs()
"""

import yaml
from pathlib import Path
from typing import Optional, List

from fivcplayground.embeddings.types.base import EmbeddingConfig
from fivcplayground.embeddings.types.repositories.base import EmbeddingConfigRepository
from fivcplayground.utils import OutputDir


class FileEmbeddingConfigRepository(EmbeddingConfigRepository):
    """
    File-based repository for embedding configurations.

    Stores all embedding configurations in a single consolidated YAML file.
    All operations are thread-safe for single-process usage.

    Storage structure:
        /<output_dir>/configs/
        └── embeddings.yaml    # All embedding configurations (mapping of embedding_id -> EmbeddingConfig)

    Attributes:
        output_dir: OutputDir instance for the repository base directory
        base_path: Path object pointing to the repository root
        embeddings_file: Path to the embeddings.yaml file

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
                       defaults to OutputDir().subdir("embeddings")

        Note:
            The base directory and configs subdirectory are created automatically
            if they don't exist.
        """
        self.output_dir = output_dir or OutputDir().subdir("configs")
        self.base_path = Path(str(self.output_dir))
        self.embeddings_file = self.base_path / "embeddings.yaml"

        # Create directories if they don't exist
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_embeddings_file(self) -> Path:
        """
        Get the file path for the consolidated embeddings YAML file.

        Returns:
            Path to embeddings.yaml file
        """
        return self.embeddings_file

    def _load_embeddings_data(self) -> dict:
        """
        Load all embeddings from the YAML file.

        Returns:
            Dictionary mapping embedding_id to embedding data. Returns empty dict if file
            doesn't exist or is corrupted.
        """
        embeddings_file = self._get_embeddings_file()

        if not embeddings_file.exists():
            return {}

        try:
            with open(embeddings_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except (yaml.YAMLError, ValueError) as e:
            print(f"Error loading embeddings from {embeddings_file.name}: {e}")
            return {}

    def _save_embeddings_data(self, embeddings_data: dict) -> None:
        """
        Save all embeddings to the YAML file.

        Args:
            embeddings_data: Dictionary mapping embedding_id to embedding data
        """
        embeddings_file = self._get_embeddings_file()
        with open(embeddings_file, "w", encoding="utf-8") as f:
            yaml.dump(embeddings_data, f, default_flow_style=False, allow_unicode=True)

    def update_embedding_config(self, embedding_config: EmbeddingConfig) -> None:
        """
        Create or update an embedding configuration.

        Stores embedding configuration in the consolidated YAML file. The embedding_id
        is derived from the embedding_config.id field.

        Args:
            embedding_config: EmbeddingConfig instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same embedding will overwrite the existing configuration.
        """
        embedding_id = embedding_config.id

        # Load existing embeddings
        embeddings_data = self._load_embeddings_data()

        # Serialize embedding config to dict
        embedding_data = embedding_config.model_dump(mode="json")

        # Update the embedding in the data
        embeddings_data[embedding_id] = embedding_data

        # Save all embeddings back to file
        self._save_embeddings_data(embeddings_data)

    def get_embedding_config(self, embedding_id: str) -> EmbeddingConfig | None:
        """
        Retrieve an embedding configuration by ID.

        Args:
            embedding_id: Unique identifier for the embedding

        Returns:
            EmbeddingConfig instance if found, None if embedding doesn't exist
            or if the YAML file is corrupted
        """
        embeddings_data = self._load_embeddings_data()

        if embedding_id not in embeddings_data:
            return None

        try:
            embedding_data = embeddings_data[embedding_id]
            embedding_data["id"] = embedding_id
            return EmbeddingConfig.model_validate(embedding_data)
        except ValueError as e:
            print(f"Error loading embedding {embedding_id}: {e}")
            return None

    def list_embedding_configs(self, **kwargs) -> List[EmbeddingConfig]:
        """
        List all embedding configurations in the repository.

        Returns:
            List of EmbeddingConfig instances sorted by embedding_id.
            Returns empty list if no embeddings exist.
        """
        embeddings_data = self._load_embeddings_data()
        embeddings = []

        # Sort by embedding_id for consistent ordering
        for embedding_id in sorted(embeddings_data.keys()):
            try:
                embedding_data = embeddings_data[embedding_id]
                embedding_data["id"] = embedding_id
                config = EmbeddingConfig.model_validate(embedding_data)
                embeddings.append(config)
            except ValueError as e:
                print(f"Error loading embedding {embedding_id}: {e}")

        return embeddings

    def delete_embedding_config(self, embedding_id: str) -> None:
        """
        Delete an embedding configuration.

        Args:
            embedding_id: Unique identifier for the embedding to delete

        Note:
            This operation is safe to call on non-existent embeddings.
        """
        embeddings_data = self._load_embeddings_data()

        if embedding_id in embeddings_data:
            del embeddings_data[embedding_id]
            self._save_embeddings_data(embeddings_data)
