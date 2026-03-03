__all__ = [
    "create_skill_retriever_async",
    "create_skill_tools_async",
    "SkillRetriever",
    "SkillConfig",
    "SkillConfigRepository",
]

import json

from fivcplayground.embeddings import (
    EmbeddingBackend,
    EmbeddingConfigRepository,
    create_embedding_db_async,
)
from fivcplayground.tools.types import (
    FunctionToolBundle,
    ToolBackend,
    ToolBundle,
)

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


async def create_skill_tools_async(
    skill_retriever: SkillRetriever,
    tool_backend: ToolBackend,
    raise_exception: bool = True,
) -> ToolBundle | None:
    """Create a FunctionToolBundle that exposes skill_find and skill_execute as agent tools."""

    async def skill_find(query: str) -> str:
        """Find skills relevant to a task using semantic search.
        Returns a JSON list of matching skills with their id and description."""
        skills = await skill_retriever.retrieve_skills_async(query)
        return json.dumps([{"id": s.id, "description": s.description} for s in skills])

    async def skill_execute(skill_id: str) -> str:
        """Execute a skill by ID. Returns its instructions, suggested tool IDs,
        and any reference resources as JSON."""
        skill = await skill_retriever.get_skill_async(skill_id)
        if not skill:
            return json.dumps({"error": f"Skill '{skill_id}' not found"})
        result: dict = {"id": skill.id}
        if skill.instructions:
            result["instructions"] = skill.instructions
        if skill.tool_ids:
            result["suggested_tool_ids"] = skill.tool_ids
        if skill.resources:
            result["resources"] = skill.resources
        return json.dumps(result)

    return FunctionToolBundle(
        name="skills",
        description="Tools for discovering and applying agent skills",
        tool_backend=tool_backend,
        tool_funcs=[skill_find, skill_execute],
    )
