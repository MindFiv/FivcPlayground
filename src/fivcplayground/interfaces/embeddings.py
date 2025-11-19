from abc import abstractmethod
from typing import Iterable, Any, Optional, List

from pydantic import BaseModel, Field
from fivcglue.interfaces import IComponent


class EmbeddingConfig(BaseModel):
    """Configuration for an embedding database."""

    provider: str = Field(default="openai", description="Embedding provider")
    model: str = Field(default="text-embedding-v3", description="Model name")
    api_key: str | None = Field(
        default=None,
        description="API key for the embedding provider",
    )
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the embedding provider",
    )


class EmbeddingDoc(BaseModel):
    """Document for embedding."""

    text: str
    metadata: Optional[dict] = None


class EmbeddingResult(EmbeddingDoc):
    """Search result with score."""

    id: Optional[str] = None
    score: Optional[float] = None


class IEmbeddingDB(IComponent):
    """Interface for embedding database."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the embedding database."""

    @property
    @abstractmethod
    def config(self) -> EmbeddingConfig:
        """Configuration of the embedding database."""

    @abstractmethod
    def add_document(self, doc: EmbeddingDoc) -> List[EmbeddingResult]:
        """Add a document to the embedding database."""

    @abstractmethod
    def get_document(self, doc_id: str) -> EmbeddingResult | None:
        """Get a document from the embedding database."""

    @abstractmethod
    def delete_document(self, doc_id: str) -> None:
        """Delete a document from the embedding database."""

    @abstractmethod
    def count_documents(self) -> int:
        """Count the number of documents in the embedding database."""

    @abstractmethod
    def clear_documents(self) -> None:
        """Clear the embedding database."""

    @abstractmethod
    def search_documents(
        self, query: str, num_documents: int = 10
    ) -> Iterable[EmbeddingResult]:
        """Search the embedding database."""


class IEmbeddingDBProvider(IComponent):
    """Interface for embedding database creation."""

    @abstractmethod
    def get_embedding_db(
        self, name: str, user_id: Optional[str] = None, **kwargs: Any
    ) -> IEmbeddingDB | None:
        """
        Get an embedding database instance.

        Args:
            name: Name of the embedding database to retrieve
            user_id: Optional user ID for multi-user support (isolates user data)
            **kwargs: Additional configuration parameters

        Returns:
            An IEmbeddingDB instance if found, None otherwise
        """

    @abstractmethod
    def list_embedding_dbs(
        self,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterable[IEmbeddingDB]:
        """
        List all available embedding databases.

        Args:
            user_id: Optional user ID for multi-user support (isolates user data)

        Returns:
            An iterable of IEmbeddingDB instances
        """
