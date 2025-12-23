from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """Configuration for an embedding function."""

    id: str = Field(..., description="Unique identifier for the embedding function")
    description: str | None = Field(
        default=None, description="Description of the embedding function"
    )
    provider: str = Field(..., description="Provider of the embedding function")
    model: str = Field(
        ...,
        description="Model name (e.g., 'text-embedding-ada-002', 'all-MiniLM-L6-v2')",
    )
    api_key: str | None = Field(
        default=None, description="API key for the embedding function (if required)"
    )
    base_url: str | None = Field(
        default=None, description="Base URL for the embedding function (if applicable)"
    )
    dimension: int = Field(
        default=1024, description="Dimension of the embedding vector"
    )


class EmbeddingTable(ABC):
    """Abstract base class for embedding tables."""

    @abstractmethod
    def add(self, text: str, metadata: dict | None = None):
        """Add text to the embedding table."""

    @abstractmethod
    def search(self, query: str, num_documents: int = 10) -> list:
        """Search the embedding table."""

    @abstractmethod
    def delete(self, metadata: dict):
        """Delete documents from the embedding table."""

    @abstractmethod
    def cleanup(self):
        """Delete all documents from the embedding table."""

    @abstractmethod
    def count(self):
        """Count the number of documents in the embedding table."""


class EmbeddingDB(ABC):
    """Abstract base class for embedding databases."""

    @abstractmethod
    def __getattr__(self, name: str) -> EmbeddingTable:
        """Get an embedding table by name."""


class EmbeddingBackend(ABC):
    """Interface for embedding backends."""

    @abstractmethod
    def create_embedding_db(
        self,
        embedding_config: EmbeddingConfig,
        space_id: str | None = None,
        **kwargs,  # ignore additional kwargs
    ) -> EmbeddingDB:
        """Create an embedding database from an EmbeddingConfig."""
