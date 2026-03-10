import inspect
import json
from typing import Callable, Awaitable

from fivcplayground import embeddings
from fivcplayground.skills.types import SkillConfig, SkillConfigRepository
from fivcplayground.tools import ToolBackend
from fivcplayground.tools.types import FunctionToolBundle


class SkillRetriever(object):
    """A semantic search-based retriever for skills."""

    def __init__(
        self,
        skill_config_repository: SkillConfigRepository | None = None,
        embedding_db: embeddings.EmbeddingDB | None = None,
        tool_backend: ToolBackend | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        assert skill_config_repository
        assert embedding_db
        # assert tool_backend

        self.max_num = 3
        self.min_sim = 0.3

        self.skill_config_repository = skill_config_repository
        self.skill_indices = embedding_db.skills
        self.tool_backend = tool_backend

    async def get_skill_async(self, skill_id: str) -> SkillConfig | None:
        """Get a skill by ID."""
        return await self.skill_config_repository.get_skill_config_async(skill_id)

    async def list_skills_async(self) -> list[SkillConfig]:
        """List all skills."""
        return await self.skill_config_repository.list_skill_configs_async()

    async def index_skills_async(self) -> None:
        """Index all skills in the embedding database."""
        self.skill_indices.cleanup()
        for skill in await self.list_skills_async():
            self.skill_indices.add(
                skill.description,
                metadata={"__skill__": skill.id},
            )

    async def retrieve_skills_async(self, query: str) -> list[SkillConfig]:
        """Retrieve skills based on a query using semantic search."""

        def score_to_sim(score: float) -> float:
            return (2.0 - score) / 2.0

        sources = self.skill_indices.search(
            query,
            num_documents=self.max_num,
        )
        skill_ids = set(
            src["metadata"]["__skill__"]
            for src in sources
            if score_to_sim(src["score"]) >= self.min_sim
        )
        skills = [await self.get_skill_async(sid) for sid in skill_ids]
        return [s for s in skills if s is not None]

    async def __call__(self, *args, **kwargs) -> list[dict]:
        skills = await self.retrieve_skills_async(*args, **kwargs)
        return [s.model_dump(mode="json") for s in skills]

    LoadCallback = (
        Callable[[SkillConfig], None] | Callable[[SkillConfig], Awaitable[None]]
    )

    def to_tool(
        self,
        skill_ids: list[str] | None = None,
        load_callback: LoadCallback | None = None,
    ) -> FunctionToolBundle:
        """Convert the retriever to a tool bundle with skill_list and skill_load.

        Args:
            skill_ids: Optional list of skill IDs to filter by.
            load_callback: Optional callback invoked when a skill is loaded.
                Callback receives SkillConfig and can be sync or async.
                Used for dynamic tool registration: callback calls
                agent_tool_span.register_tool_async() for skill.tool_ids

        Returns:
            FunctionToolBundle with two functions:
            - skill_list() → JSON list of {id, description}
            - skill_load(skill_id) → JSON with full skill details, triggers callback if provided

        Example:
            async def _extend_tools(skill: SkillConfig):
                for tool_id in skill.tool_ids or []:
                    for tool in await agent_tool_span.register_tool_async(tool_id):
                        agent.tool_registry.register_dynamic_tool(tool)

            bundle = skill_retriever.to_tool(load_callback=_extend_tools)
        """
        assert self.tool_backend

        async def skill_list() -> str:
            """List all available skills with their id and description."""
            skills = (
                [await self.get_skill_async(sid) for sid in skill_ids]
                if skill_ids is not None
                else await self.list_skills_async()
            )
            return json.dumps(
                [
                    s.model_dump(mode="json", include={"id", "description"})
                    for s in skills
                    if s is not None
                ]
            )

        async def skill_load(skill_id: str) -> str:
            """Load a skill by ID."""
            skill = await self.get_skill_async(skill_id)
            if not skill:
                return json.dumps({"error": f"Skill '{skill_id}' not found"})

            if load_callback:
                result = load_callback(skill)
                if inspect.iscoroutine(result):
                    await result

            return json.dumps(skill.model_dump(mode="json"))

        return FunctionToolBundle(
            name="skills",
            description="Tools for listing and loading skills",
            tool_backend=self.tool_backend,
            tool_funcs=[skill_list, skill_load],
        )
