from typing import Optional

from fivcplayground import settings, utils
from fivcplayground.embeddings.types import (
    EmbeddingDB,
    EmbeddingFunction,
)


def _openai_embedding_function(*args, **kwargs) -> EmbeddingFunction:
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    return OpenAIEmbeddingFunction(
        api_key=kwargs.get("api_key", ""),
        api_base=kwargs.get("base_url", ""),
        model_name=kwargs.get("model", ""),
    )


def _ollama_embedding_function(*args, **kwargs) -> EmbeddingFunction:
    from chromadb.utils.embedding_functions import OllamaEmbeddingFunction

    return OllamaEmbeddingFunction(
        url=kwargs.get("base_url", ""),
        model_name=kwargs.get("model", ""),
    )


def create_embedding_function(*args, **kwargs) -> EmbeddingFunction:
    """Create a default embedding function for chromadb."""
    kwargs = settings.DEFAULT_EMBEDDING_ARGS(kwargs)

    model_provider = kwargs.pop("provider")
    if not model_provider:
        raise AssertionError("provider not specified")

    if model_provider == "openai":
        return _openai_embedding_function(*args, **kwargs)
    if model_provider == "ollama":
        return _ollama_embedding_function(*args, **kwargs)
    else:
        # Default to sentence transformer
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )

        return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


def create_embedding_db(
    *args,
    function: Optional[EmbeddingFunction] = None,
    output_dir: Optional[utils.OutputDir] = None,
    **kwargs,
) -> EmbeddingDB:
    """Create a default embedding database for chromadb."""
    return EmbeddingDB(
        output_dir=output_dir,
        function=function or create_embedding_function(**kwargs),
    )


default_embedding_db = utils.LazyValue(lambda: create_embedding_db())
