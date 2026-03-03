__all__ = [
    "create_skill_retriever_async",
    "SkillRetriever",
    "SkillConfig",
    "SkillConfigRepository",
]

from fivcplayground.embeddings import (
    EmbeddingBackend,
    EmbeddingConfigRepository,
    create_embedding_db_async,
)
from fivcplayground.tools.types import ToolBackend

from .types import SkillConfig, SkillConfigRepository, SkillRetriever


async def create_skill_retriever_async(
    skill_config_repository: SkillConfigRepository | None = None,
    embedding_backend: EmbeddingBackend | None = None,
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
    space_id: str | None = None,
    raise_exception: bool = True,
    tool_backend: ToolBackend | None = None,
    **kwargs,  # ignore additional kwargs
) -> SkillRetriever | None:
    """Create a SkillRetriever with semantic search capability."""
    if not skill_config_repository:
        if raise_exception:
            raise RuntimeError("No skill config repository specified")
        return None

    if not embedding_config_repository:
        if raise_exception:
            raise RuntimeError("No embedding config repository specified")
        return None

    embedding_db = await create_embedding_db_async(
        embedding_backend=embedding_backend,
        embedding_config_repository=embedding_config_repository,
        embedding_config_id=embedding_config_id,
        space_id=space_id,
        raise_exception=raise_exception,
    )
    if not embedding_db:
        if raise_exception:
            raise RuntimeError(f"Embedding not found {embedding_config_id}")
        return None

    return SkillRetriever(
        skill_config_repository=skill_config_repository,
        embedding_db=embedding_db,
        tool_backend=tool_backend,
    )
