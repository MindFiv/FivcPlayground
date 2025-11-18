from abc import abstractmethod
from typing import Iterable, Any, Optional, List

from pydantic import BaseModel
from fivcglue.interfaces import IComponent


class IEmbeddingDoc(BaseModel):
    """Document for embedding."""

    text: str
    metadata: Optional[dict] = None


class IEmbeddingResult(IEmbeddingDoc):
    """Search result with score."""

    id: Optional[str] = None
    score: Optional[float] = None


class IEmbeddingDB(IComponent):
    """Interface for embedding database."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the embedding database."""

    @abstractmethod
    def add_document(self, doc: IEmbeddingDoc) -> List[IEmbeddingResult]:
        """Add a document to the embedding database."""

    @abstractmethod
    def get_document(self, doc_id: str) -> IEmbeddingResult | None:
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
    ) -> Iterable[IEmbeddingResult]:
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
