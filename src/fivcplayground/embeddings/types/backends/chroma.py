from typing import Dict, Any

import chromadb

from langchain_text_splitters import RecursiveCharacterTextSplitter

from fivcplayground.embeddings.types.base import EmbeddingConfig
from fivcplayground.utils import OutputDir


def _create_embedding_function(
    embedding_config: EmbeddingConfig,
) -> chromadb.EmbeddingFunction:
    if embedding_config.provider == "openai":
        from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

        return OpenAIEmbeddingFunction(
            api_key=embedding_config.api_key,
            api_base=embedding_config.base_url,
            model_name=embedding_config.model,
        )

    elif embedding_config.provider == "ollama":
        from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

        return OllamaEmbeddingFunction(
            url=embedding_config.base_url,
            model_name=embedding_config.model,
        )

    else:
        raise ValueError(f"Unknown provider {embedding_config.provider}")


class EmbeddingDB(object):
    """
    EmbeddingDB is a wrapper around the ChromaDB embedding database.

    Supports embedding space isolation via the space_id parameter, allowing
    multiple isolated namespaces within a single ChromaDB instance.
    """

    def __init__(
        self,
        embedding_config: EmbeddingConfig,
        output_dir: OutputDir | None = None,
        space_id: str | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        """
        Initialize the EmbeddingDB.

        Args:
            embedding_config: Configuration for the embedding model
            output_dir: Optional output directory for ChromaDB persistence
            space_id: Optional embedding space identifier for data isolation.
                     If None, defaults to "default" (shared/backward-compatible space).
                     Examples: "user_alice", "project_website", "env_staging"
            **kwargs: Additional arguments (ignored)
        """
        output_dir = output_dir or OutputDir().subdir("db")
        self.db = chromadb.PersistentClient(path=str(output_dir))
        self.function = _create_embedding_function(embedding_config)
        self.space_id = space_id or "default"

    def __getattr__(self, name: str) -> "EmbeddingTable":
        """
        Dynamically create EmbeddingTable instances for collections.

        Collection names are automatically namespaced by space_id:
        - space_id="default": collection name = "tools"
        - space_id="user_alice": collection name = "tools_user_alice"

        Args:
            name: Base collection name (e.g., "tools")

        Returns:
            EmbeddingTable instance for the space-specific collection
        """
        # Incorporate space_id into collection name
        collection_name = (
            f"{name}_{self.space_id}" if self.space_id != "default" else name
        )
        return EmbeddingTable(
            self.db.get_or_create_collection(
                collection_name,
                embedding_function=self.function,
            )
        )


class EmbeddingTable(object):
    """
    EmbeddingTable is a wrapper around a ChromaDB collection.
    """

    def __init__(self, collection: chromadb.Collection):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=100
        )
        self.collection = collection

    def add(self, text: str, metadata: Dict[str, Any] | None = None):
        """Add text to the collection."""
        chunks = self.text_splitter.split_text(text)
        self.collection.add(
            documents=chunks,
            metadatas=([metadata] * len(chunks)) if metadata else None,
            ids=[str(hash(chunk)) for chunk in chunks],
        )

    def delete(self, metadata: Dict[str, Any]):
        """Delete documents from the collection."""
        if not metadata:
            raise ValueError("metadata is required")

        where_clauses = [{key: {"$eq": value}} for key, value in metadata.items()]
        if len(where_clauses) == 1:
            where = where_clauses[0]
        else:
            where = {"$and": where_clauses}

        self.collection.delete(where=where)

    def search(self, query: str, num_documents: int = 10) -> list:
        """Search the collection."""
        results = self.collection.query(query_texts=[query], n_results=num_documents)
        result_docs = results["documents"][0]
        result_metas = results["metadatas"][0]
        result_scores = results["distances"][0]
        return [
            {"text": doc, "metadata": meta, "score": score}
            for doc, meta, score in zip(result_docs, result_metas, result_scores)
        ]

    def cleanup(self):
        """Delete the collection."""
        while True:
            ids2delete = self.collection.peek(limit=100)["ids"]
            if not ids2delete:
                break
            self.collection.delete(ids=ids2delete)

    def count(self):
        """Count the number of documents in the collection."""
        return self.collection.count()
