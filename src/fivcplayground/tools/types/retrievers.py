import json

from fivcplayground import embeddings
from fivcplayground.tools.types.base import (
    Tool,
    ToolBackend,
)
from fivcplayground.tools.types.repositories.base import (
    ToolConfigRepository,
)


class ToolRetriever(object):
    """A semantic search-based retriever for tools."""

    def __init__(
        self,
        tool_backend: ToolBackend | None = None,
        tools: list[Tool] | None = None,  # for builtin tools
        tool_config_repository: ToolConfigRepository | None = None,
        embedding_db: embeddings.EmbeddingDB | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        """Initialize the ToolRetriever."""
        assert tool_backend
        assert tool_config_repository
        assert embedding_db

        self.max_num = 5  # top k
        self.min_sim = 0.3  # min similarity

        self.tool_config_repository = tool_config_repository
        self.tool_backend = tool_backend
        self.tool_indices = embedding_db.tools

        self.tools: dict[str, Tool] = {t.name: t for t in tools} if tools else {}
        # add self to tools
        self.tools.update(tool_retriever=self.to_tool())

    def __str__(self):
        return f"ToolRetriever(num_tools={len(self.tools)})"

    @property
    def retrieve_min_sim(self):
        return self.min_sim

    @retrieve_min_sim.setter
    def retrieve_min_sim(self, value: float):
        self.min_sim = value

    @property
    def retrieve_max_num(self):
        return self.max_num

    @retrieve_max_num.setter
    def retrieve_max_num(self, value: int):
        self.max_num = value

    async def get_tool_async(self, name: str) -> Tool | None:
        """Get a tool by name (async version)."""
        tool = self.tools.get(name)
        if tool:
            return tool

        tool_config = await self.tool_config_repository.get_tool_config_async(name)
        return (
            self.tool_backend.create_tool_bundle(tool_config) if tool_config else None
        )

    async def list_tools_async(self) -> list[Tool]:
        """List all tools (async version)."""
        tools = list(self.tools.values())
        tool_configs = await self.tool_config_repository.list_tool_configs_async()
        tools.extend([self.tool_backend.create_tool_bundle(c) for c in tool_configs])
        return tools

    async def index_tools_async(self):
        """Index all tools in the retriever (async version)."""

        # cleanup the indices
        self.tool_indices.cleanup()

        # rebuild indices
        for tool in await self.list_tools_async():
            tool_name = tool.name
            tool_desc = tool.description
            self.tool_indices.add(
                tool_desc,
                metadata={"__tool__": tool_name},
            )

    async def retrieve_tools_async(self, query: str, **kwargs) -> list[Tool]:
        """Retrieve tools based on a query (async version)."""

        def score_to_sim(score: float) -> float:
            return (2.0 - score) / 2.0

        sources = self.tool_indices.search(
            query,
            num_documents=self.retrieve_max_num,
        )

        tool_names = set(
            src["metadata"]["__tool__"]
            for src in sources
            if score_to_sim(src["score"]) >= self.retrieve_min_sim
        )
        # print("==" * 20)
        # print(f"query: {query}")
        # print(f"{sources} tools found")
        tools = [await self.get_tool_async(name) for name in tool_names]
        return [t for t in tools if t is not None]

    async def __call__(self, *args, **kwargs) -> list[dict]:
        tools = await self.retrieve_tools_async(*args, **kwargs)
        return [{"name": t.name, "description": t.description} for t in tools]

    def to_tool(self, dummy: bool = False) -> Tool:
        """Convert the retriever to a tool."""
        if dummy:

            async def _func() -> str:
                """A dummy tool that does nothing."""
                return "Hi there! nothing happened."

            return self.tool_backend.create_tool(
                _func, "dummy_tool", "A dummy tool that does nothing."
            )

        else:

            async def _func(query: str) -> str:
                """Use this tool to retrieve the best tools for a given task"""
                # Use __call__ to get tool metadata (name and description) instead of
                # the full BaseTool objects, which can cause infinite recursion when
                # converting to string due to circular references in Pydantic models
                return json.dumps(await self.__call__(query))

            return self.tool_backend.create_tool(
                _func, "tool_retriever", "A tool to retrieve tools."
            )
