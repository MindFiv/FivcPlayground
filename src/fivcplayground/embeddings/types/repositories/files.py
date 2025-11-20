"""
File-based embedding configuration repository implementation.

This module provides FileEmbeddingConfigRepository, a file-based implementation
of EmbeddingConfigRepository that stores embedding configurations in a hierarchical
directory structure with JSON files.

Storage Structure:
    /<output_dir>/
    └── embedding_<embedding_id>.json    # Embedding configuration (EmbeddingConfig)

This structure allows for:
    - Simple file-based storage
    - Easy inspection of embedding data
    - Human-readable JSON format
    - Simple backup and version control

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
    ...     model_id="text-embedding-ada-002",
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

import json
from pathlib import Path
from typing import Optional, List, Any

from fivcplayground.embeddings.types.base import EmbeddingConfig
from fivcplayground.embeddings.types.repositories.base import EmbeddingConfigRepository
from fivcplayground.utils import OutputDir


class FileEmbeddingConfigRepository(EmbeddingConfigRepository):
    """
    File-based repository for embedding configurations.

    Stores embedding configurations in JSON files within a directory structure.
    All operations are thread-safe for single-process usage.

    Storage structure:
        /<output_dir>/
        └── embedding_<embedding_id>.json    # Embedding configuration

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
                       defaults to OutputDir().subdir("embeddings")

        Note:
            The base directory is created automatically if it doesn't exist.
        """
        self.output_dir = output_dir or OutputDir().subdir("embeddings")
        self.base_path = Path(str(self.output_dir))
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_embedding_file(self, embedding_id: str) -> Path:
        """
        Get the file path for an embedding configuration.

        Args:
            embedding_id: Embedding identifier

        Returns:
            Path to embedding configuration file (e.g., /<base_path>/embedding_<embedding_id>.json)
        """
        return self.base_path / f"embedding_{embedding_id}.json"

    def update_embedding_config(self, embedding_config: EmbeddingConfig) -> None:
        """
        Create or update an embedding configuration.

        Stores embedding configuration in a JSON file. The embedding_id is derived from
        the embedding_config.id field.

        Args:
            embedding_config: EmbeddingConfig instance to persist

        Note:
            This operation is idempotent - calling it multiple times with the
            same embedding will overwrite the existing configuration.
        """
        embedding_id = embedding_config.id
        embedding_file = self._get_embedding_file(embedding_id)

        # Serialize embedding config to JSON
        embedding_data = embedding_config.model_dump(mode="json")

        with open(embedding_file, "w", encoding="utf-8") as f:
            json.dump(embedding_data, f, indent=2, ensure_ascii=False)

    def get_embedding_config(self, embedding_id: str) -> EmbeddingConfig | None:
        """
        Retrieve an embedding configuration by ID.

        Args:
            embedding_id: Unique identifier for the embedding

        Returns:
            EmbeddingConfig instance if found, None if embedding doesn't exist
            or if the JSON file is corrupted
        """
        embedding_file = self._get_embedding_file(embedding_id)

        if not embedding_file.exists():
            return None

        try:
            with open(embedding_file, "r", encoding="utf-8") as f:
                embedding_data = json.load(f)

            return EmbeddingConfig.model_validate(embedding_data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading embedding {embedding_id}: {e}")
            return None

    def list_embedding_configs(self, **kwargs) -> List[EmbeddingConfig]:
        """
        List all embedding configurations in the repository.

        Returns:
            List of EmbeddingConfig instances sorted by embedding_id.
            Returns empty list if no embeddings exist.
        """
        embeddings = []

        if not self.base_path.exists():
            return embeddings

        for embedding_file in sorted(self.base_path.glob("embedding_*.json")):
            try:
                with open(embedding_file, "r", encoding="utf-8") as f:
                    embedding_data = json.load(f)
                config = EmbeddingConfig.model_validate(embedding_data)
                embeddings.append(config)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading embedding from {embedding_file.name}: {e}")

        return embeddings

    def delete_embedding_config(self, embedding_id: str) -> None:
        """
        Delete an embedding configuration.

        Args:
            embedding_id: Unique identifier for the embedding to delete

        Note:
            This operation is safe to call on non-existent embeddings.
        """
        embedding_file = self._get_embedding_file(embedding_id)
        if embedding_file.exists():
            embedding_file.unlink()

    def filter_repository(
        self,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> "FileEmbeddingConfigRepository":
        """Filter the repository.

        Args:
            user_id: Optional user ID to filter by
            kwargs: Additional keyword arguments for filtering

        Returns:
            Filtered repository
        """
        return self
