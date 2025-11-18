"""
ChromaDB-based embeddings implementations for FivcPlayground.

This module provides implementations of IEmbeddingDB and IEmbeddingDBProvider interfaces,
enabling flexible ChromaDB-based embeddings management through the component architecture.

Classes:
    EmbeddingsImpl: Implementation of IEmbeddingDB interface for ChromaDB collections
    EmbeddingsProviderImpl: Implementation of IEmbeddingDBProvider interface for embeddings creation
"""

from typing import Any, Iterable, Optional, List

import chromadb
from chromadb.utils.embedding_functions import EmbeddingFunction
from langchain_text_splitters import RecursiveCharacterTextSplitter

from fivcglue import IComponentSite
from fivcglue.interfaces.utils import query_component

from fivcplayground.interfaces import (
    IEmbeddingDB,
    IEmbeddingDBProvider,
    IEmbeddingDoc,
    IEmbeddingResult,
    ISettingProvider,
)
from fivcplayground.utils import OutputDir

# ChromaDB exception types for specific error handling
try:
    from chromadb.errors import InvalidCollectionException
except ImportError:
    # Fallback if chromadb.errors is not available in older versions
    InvalidCollectionException = Exception  # type: ignore


def _create_embedding_function(provider: str = "openai", **kwargs: Any) -> Any:
    """
    Create an embedding function based on provider type.

    Routes embedding function creation to the appropriate provider-specific function.

    Args:
        provider: The embedding provider ("openai", "ollama", or "default")
        **kwargs: Provider-specific configuration parameters

    Returns:
        An embedding function instance

    Raises:
        ValueError: If the provider is not supported
    """
    if provider == "openai":
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        return OpenAIEmbeddingFunction(
            api_key=kwargs.get("api_key", ""),
            api_base=kwargs.get("base_url", "https://api.openai.com/v1"),
            model_name=kwargs.get("model", "text-embedding-3-small"),
        )
    elif provider == "ollama":
        from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

        return OllamaEmbeddingFunction(
            url=kwargs.get("base_url", "http://localhost:11434"),
            model_name=kwargs.get("model", "nomic-embed-text"),
        )
    else:
        # Default to sentence transformer
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )

        return SentenceTransformerEmbeddingFunction(
            model_name=kwargs.get("model", "all-MiniLM-L6-v2")
        )


class EmbeddingsImpl(IEmbeddingDB):
    """
    Implementation of IEmbeddingDB interface with ChromaDB backend.

    This class represents a single embeddings collection with lazy-loaded access
    to the underlying ChromaDB collection. The actual collection instantiation
    is deferred until first access. Uses ChromaDB's native API directly without
    wrapper classes.

    Example:
        >>> embeddings = EmbeddingsImpl("documents", db_client, embedding_function)
        >>> doc = IEmbeddingDoc(text="Hello world", metadata={"source": "test"})
        >>> chunk_results = embeddings.add_document(doc)  # Returns list of IEmbeddingResult
        >>> for result in chunk_results:
        ...     print(f"Added chunk: {result.id}")
        >>> search_results = list(embeddings.search_documents("hello", num_documents=5))
    """

    def __init__(
        self,
        name: str,
        db_client: chromadb.PersistentClient,
        embedding_function: EmbeddingFunction,
        **config: Any,
    ):
        """
        Initialize an embeddings instance with lazy loading.

        Args:
            name: Name of the embeddings collection (e.g., "documents", "knowledge_base")
            db_client: ChromaDB PersistentClient instance for database access
            embedding_function: ChromaDB embedding function for vector generation
            **config: Additional configuration parameters (stored for future use)
        """
        self._name = name
        self._db_client = db_client
        self._embedding_function = embedding_function
        self._config = config
        self._collection = None  # Lazy-loaded on first access
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=100
        )

    @property
    def name(self) -> str:
        """Get the name of the embeddings collection."""
        return self._name

    def _get_collection(self) -> chromadb.Collection:
        """
        Get the underlying ChromaDB collection with lazy loading.

        On first call, retrieves or creates the ChromaDB collection and caches it.

        Returns:
            The underlying chromadb.Collection instance

        Raises:
            ValueError: If collection name is invalid
            RuntimeError: If ChromaDB client is unavailable or collection creation fails
        """
        if self._collection is None:
            try:
                self._collection = self._db_client.get_or_create_collection(
                    self._name,
                    embedding_function=self._embedding_function,
                )
            except (ValueError, TypeError) as e:
                # ValueError: Invalid collection name or parameters
                # TypeError: Invalid parameter types
                raise ValueError(
                    f"Failed to create collection '{self._name}': {e}"
                ) from e
            except (AttributeError, RuntimeError) as e:
                # AttributeError: db_client doesn't have expected methods
                # RuntimeError: ChromaDB internal errors
                raise RuntimeError(
                    f"ChromaDB client error for collection '{self._name}': {e}"
                ) from e
        return self._collection

    def add_document(self, doc: IEmbeddingDoc) -> List[IEmbeddingResult]:
        """
        Add a document to the embeddings collection.

        The document is split into chunks and stored in ChromaDB with metadata.
        Each chunk is stored separately with its own ID generated by ChromaDB.

        Args:
            doc: IEmbeddingDoc instance containing text and optional metadata

        Returns:
            A list of IEmbeddingResult objects, one for each chunk created from the document.
            Each result contains the chunk's ID, text, metadata, and score (1.0 for newly added chunks).
            Returns an empty list [] on failure.

        Handles:
            ValueError: Invalid document text or metadata
            TypeError: Invalid parameter types for ChromaDB add()
            RuntimeError: ChromaDB collection errors
        """
        try:
            collection = self._get_collection()
            # Split text into chunks
            chunks = self._text_splitter.split_text(doc.text)

            # Generate IDs for each chunk
            chunk_ids = [str(hash(chunk)) for chunk in chunks]

            # Add to collection with ChromaDB's native API
            collection.add(
                documents=chunks,
                metadatas=([doc.metadata] * len(chunks)) if doc.metadata else None,
                ids=chunk_ids,
            )

            # Create IEmbeddingResult for each chunk
            results = [
                IEmbeddingResult(
                    id=chunk_id,
                    text=chunk,
                    metadata=doc.metadata,
                    score=1.0,  # Perfect score for newly added chunks
                )
                for chunk_id, chunk in zip(chunk_ids, chunks)
            ]

            return results
        except (ValueError, TypeError, RuntimeError):
            # Graceful failure: return empty list on expected errors
            # ValueError: Invalid document text or metadata
            # TypeError: Invalid parameter types
            # RuntimeError: ChromaDB collection errors
            return []

    def get_document(self, doc_id: str) -> IEmbeddingResult | None:
        """
        Get a document by ID from the embeddings collection.

        Retrieves a document directly from ChromaDB using its native get() method.

        Args:
            doc_id: The document ID to retrieve

        Returns:
            IEmbeddingResult if found, None otherwise

        Handles:
            ValueError: Invalid document ID format
            KeyError: Document not found in collection
            RuntimeError: ChromaDB collection errors
        """
        try:
            collection = self._get_collection()
            # Use ChromaDB's native get() method to retrieve document
            result = collection.get(ids=[doc_id])

            if not result or not result.get("documents"):
                return None

            return IEmbeddingResult(
                id=doc_id,
                text=result["documents"][0] if result["documents"] else "",
                metadata=result["metadatas"][0] if result.get("metadatas") else None,
                score=1.0,
            )
        except (ValueError, KeyError, RuntimeError):
            # Graceful failure: return None on expected errors
            # ValueError: Invalid document ID
            # KeyError: Document not found
            # RuntimeError: ChromaDB collection errors
            return None

    def delete_document(self, doc_id: str) -> None:
        """
        Delete a document from the embeddings collection.

        Deletes a document directly from ChromaDB using its native delete() method.

        Args:
            doc_id: The document ID to delete

        Handles:
            ValueError: Invalid document ID format
            KeyError: Document not found in collection
            RuntimeError: ChromaDB collection errors
        """
        try:
            collection = self._get_collection()
            # Use ChromaDB's native delete() method
            collection.delete(ids=[doc_id])
        except (ValueError, KeyError, RuntimeError):
            # Graceful failure: silently ignore expected errors
            # ValueError: Invalid document ID
            # KeyError: Document not found (not an error condition)
            # RuntimeError: ChromaDB collection errors
            pass

    def count_documents(self) -> int:
        """
        Count the number of documents in the embeddings collection.

        Returns:
            The number of documents in the collection, or 0 on error

        Handles:
            RuntimeError: ChromaDB collection errors
            AttributeError: Collection doesn't have count() method
        """
        try:
            collection = self._get_collection()
            return collection.count()
        except (RuntimeError, AttributeError):
            # Graceful failure: return 0 on expected errors
            # RuntimeError: ChromaDB collection errors
            # AttributeError: Collection doesn't have count() method
            return 0

    def clear_documents(self) -> None:
        """
        Clear all documents from the embeddings collection.

        Handles:
            RuntimeError: ChromaDB collection errors
            KeyError: Collection doesn't have expected structure
            AttributeError: Collection doesn't have peek() or delete() methods
        """
        try:
            collection = self._get_collection()
            # Delete all documents in batches
            while True:
                ids_to_delete = collection.peek(limit=100)["ids"]
                if not ids_to_delete:
                    break
                collection.delete(ids=ids_to_delete)
        except (RuntimeError, KeyError, AttributeError):
            # Graceful failure: silently ignore expected errors
            # RuntimeError: ChromaDB collection errors
            # KeyError: Collection doesn't have expected structure
            # AttributeError: Collection doesn't have peek() or delete() methods
            pass

    def search_documents(
        self, query: str, num_documents: int = 10
    ) -> Iterable[IEmbeddingResult]:
        """
        Search the embeddings collection for similar documents.

        Args:
            query: The search query text
            num_documents: Maximum number of results to return (default: 10)

        Returns:
            An iterable of IEmbeddingResult instances with search results

        Handles:
            ValueError: Invalid query text or num_documents parameter
            KeyError: Query results don't have expected structure
            RuntimeError: ChromaDB collection errors
            AttributeError: Collection doesn't have query() method
        """
        try:
            collection = self._get_collection()
            # Use ChromaDB's native query method
            results = collection.query(query_texts=[query], n_results=num_documents)

            result_docs = results["documents"][0] if results["documents"] else []
            result_metas = results["metadatas"][0] if results["metadatas"] else []
            result_scores = results["distances"][0] if results["distances"] else []

            for doc, meta, score in zip(result_docs, result_metas, result_scores):
                yield IEmbeddingResult(
                    text=doc,
                    metadata=meta,
                    score=score,
                )
        except (ValueError, KeyError, RuntimeError, AttributeError):
            # Return empty iterable on expected errors
            # ValueError: Invalid query text or parameters
            # KeyError: Query results don't have expected structure
            # RuntimeError: ChromaDB collection errors
            # AttributeError: Collection doesn't have query() method
            return


class EmbeddingsProviderImpl(IEmbeddingDBProvider):
    """
    Implementation of IEmbeddingDBProvider interface for ChromaDB embeddings.

    This class provides access to ChromaDB embeddings collections configured through
    the settings provider. It loads embeddings configurations from settings and creates
    embeddings instances on demand without caching to support multi-user scenarios.

    The provider expects settings to be organized with embeddings names as keys and
    configuration dictionaries as values. Each configuration should include:
    - provider: The embedding provider (e.g., "openai", "ollama", "default")
    - model: The model name (e.g., "text-embedding-3-small", "nomic-embed-text")
    - Additional provider-specific parameters (api_key, base_url, etc.)

    Multi-user support:
    - Pass user_id to get_embedding_db() and list_embedding_dbs() for user-specific data isolation
    - Each user's embeddings are isolated by using user-specific configuration from settings

    Example:
        >>> from fivcplayground.settings import default_component_site
        >>> from fivcplayground.interfaces import IEmbeddingDBProvider
        >>> provider = default_component_site.get_component(IEmbeddingDBProvider)
        >>> embeddings = provider.get_embedding_db("documents", user_id="user123")
        >>> if embeddings:
        ...     print(f"Embeddings: {embeddings.name}")

    Configuration file example (settings.yaml):
        documents:
          provider: openai
          model: text-embedding-3-small
          api_key: sk-...
        knowledge_base:
          provider: ollama
          model: nomic-embed-text
          base_url: http://localhost:11434
    """

    def __init__(self, component_site: IComponentSite, **kwargs: Any):
        """
        Initialize the embeddings provider.

        Args:
            component_site: An IComponentSite instance for component registration
            **kwargs: Additional keyword arguments (output_dir for custom database path)
        """
        self._component_site = component_site
        self._setting_provider = query_component(
            component_site,
            ISettingProvider,
            "embeddings",
        )
        self._db_clients = {}  # Cache for ChromaDB clients per output_dir
        self._output_dir = kwargs.get("output_dir", None)

    def _get_db_client(
        self, output_dir: Optional[str] = None
    ) -> chromadb.PersistentClient:
        """
        Get or create a ChromaDB PersistentClient with lazy loading.

        Args:
            output_dir: Optional custom output directory for the database

        Returns:
            A chromadb.PersistentClient instance

        Raises:
            ValueError: If output_dir is invalid or inaccessible
            RuntimeError: If ChromaDB client initialization fails
        """
        if output_dir is None:
            output_dir = (
                self._output_dir
                if self._output_dir
                else str(OutputDir().subdir("embeddings"))
            )

        if output_dir not in self._db_clients:
            try:
                self._db_clients[output_dir] = chromadb.PersistentClient(
                    path=output_dir
                )
            except (ValueError, TypeError, OSError) as e:
                # ValueError: Invalid path format
                # TypeError: Invalid parameter types
                # OSError: Directory doesn't exist or is inaccessible
                raise RuntimeError(
                    f"Failed to create ChromaDB client at '{output_dir}': {e}"
                ) from e

        return self._db_clients[output_dir]

    def get_embedding_db(
        self, name: str, user_id: Optional[str] = None, **kwargs: Any
    ) -> IEmbeddingDB | None:
        """
        Get an embedding database instance by name with lazy loading.

        Retrieves the embeddings configuration from settings and returns an EmbeddingsImpl
        instance with lazy loading. The actual collection instantiation is deferred
        until first access. Instances are created on-demand without caching to support
        multi-user scenarios.

        Args:
            name: Name of the embedding database to retrieve (e.g., "documents", "knowledge_base")
            user_id: Optional user ID for multi-user support (isolates user data)
            **kwargs: Additional configuration parameters (overrides settings)

        Returns:
            An EmbeddingsImpl instance if the embedding database exists and can be configured,
            None otherwise. Returns None if the embedding database name is not found in settings
            or if configuration retrieval fails.
        """
        # Get embeddings configuration from settings
        if self._setting_provider is None:
            return None

        setting = self._setting_provider.get_setting(
            name,
            user_id=user_id,
            **kwargs,
        )
        if setting is None:
            return None

        try:
            # Build configuration from setting
            config = {}
            for key, value in setting.list():
                config[key] = value

            # Override with any provided kwargs
            config.update(kwargs)

            # Get provider and model info
            provider = config.get("provider", "default")
            embedding_function = _create_embedding_function(provider, **config)

            # Get or create ChromaDB client
            db_client = self._get_db_client()

            # Create EmbeddingsImpl with lazy loading (collection creation deferred)
            # Create a user-specific collection name if user_id is provided
            collection_name = f"{name}_{user_id}" if user_id else name
            embeddings = EmbeddingsImpl(
                collection_name, db_client, embedding_function, **config
            )

            return embeddings
        except (AttributeError, TypeError, ValueError, RuntimeError) as e:
            # Graceful failure: return None on configuration errors
            # AttributeError: setting doesn't have list() method
            # TypeError: iteration over setting.list() fails or invalid parameter types
            # ValueError: invalid configuration values
            # RuntimeError: ChromaDB client creation failed
            raise RuntimeError(f'Failed to create embeddings "{name}": {e}') from e

    def list_embedding_dbs(
        self,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterable[IEmbeddingDB]:
        """
        List all available embedding databases.

        Iterates through all settings and attempts to create embedding database instances
        for each one. Embedding databases that fail to create are skipped. Supports multi-user
        scenarios by isolating embedding databases per user.

        Args:
            user_id: Optional user ID for multi-user support (isolates user data)

        Returns:
            An iterable of EmbeddingsImpl instances for all successfully created embedding databases.
        """
        if self._setting_provider is None:
            return

        for setting in self._setting_provider.list_settings(
            user_id=user_id,
            **kwargs,
        ):
            embeddings = self.get_embedding_db(
                setting.name,
                user_id=user_id,
                **kwargs,
            )
            if embeddings is not None:
                yield embeddings
