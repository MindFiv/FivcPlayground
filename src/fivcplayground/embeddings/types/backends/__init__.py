__all__ = [
    "EmbeddingDB",
    "EmbeddingTable",
]

from fivcplayground import __embedding_backend__

if __embedding_backend__ == "chroma":
    from .chroma import EmbeddingDB, EmbeddingTable

else:
    raise NotImplementedError(f"Unknown embedding backend: {__embedding_backend__}")
