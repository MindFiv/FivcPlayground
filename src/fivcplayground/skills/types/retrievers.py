from fivcplayground import embeddings
from fivcplayground.skills.types.base import SkillConfig
from fivcplayground.skills.types.repositories.base import SkillConfigRepository


class SkillRetriever(object):
    """A semantic search-based retriever for skills."""

    def __init__(
        self,
        skill_config_repository: SkillConfigRepository | None = None,
        embedding_db: embeddings.EmbeddingDB | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        assert skill_config_repository
        assert embedding_db

        self.max_num = 3
        self.min_sim = 0.3

        self.skill_config_repository = skill_config_repository
        self.skill_indices = embedding_db.skills

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
        tools = await self.retrieve_skills_async(*args, **kwargs)
        return [{"name": t.id, "description": t.description} for t in tools]
