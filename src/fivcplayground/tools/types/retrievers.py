import json
from typing_extensions import deprecated

from pydantic import BaseModel, Field
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
        tool_list: list[Tool] | None = None,  # for builtin tools
        tool_config_repository: ToolConfigRepository | None = None,
        embedding_db: embeddings.EmbeddingDB | None = None,
        **kwargs,  # ignore additional kwargs
    ):
        """Initialize the ToolRetriever."""
        assert tool_backend
        assert tool_config_repository
        assert embedding_db

        # if tool_config_repository is None:
        #     from fivcplayground.tools.types.repositories.files import (
        #         FileToolConfigRepository,
        #     )
        #
        #     tool_config_repository = FileToolConfigRepository()

        self.max_num = 10  # top k
        self.min_score = 0.0  # min score

        self.tools: dict[str, Tool] = (
            {t.name: t for t in tool_list} if tool_list else {}
        )
        self.tool_config_repository = tool_config_repository
        self.tool_backend = tool_backend
        self.tool_indices = embedding_db.tools

    def __str__(self):
        return f"ToolRetriever(num_tools={len(self.tools)})"

    @property
    def retrieve_min_score(self):
        return self.min_score

    @retrieve_min_score.setter
    def retrieve_min_score(self, value: float):
        self.min_score = value

    @property
    def retrieve_max_num(self):
        return self.max_num

    @retrieve_max_num.setter
    def retrieve_max_num(self, value: int):
        self.max_num = value

    @deprecated("Use get_tool_async instead")
    def get_tool(self, name: str) -> Tool | None:
        import asyncio

        return asyncio.run(self.get_tool_async(name))

    @deprecated("Use list_tools_async instead")
    def list_tools(self) -> list[Tool]:
        import asyncio

        return asyncio.run(self.list_tools_async())

    @deprecated("Use index_tools_async instead")
    def index_tools(self):
        import asyncio

        asyncio.run(self.index_tools_async())

    @deprecated("Use retrieve_tools_async instead")
    def retrieve_tools(self, query: str, **kwargs) -> list[Tool]:
        import asyncio

        return asyncio.run(self.retrieve_tools_async(query, **kwargs))

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
        sources = self.tool_indices.search(
            query,
            num_documents=self.retrieve_max_num,
        )

        tool_names = set(
            src["metadata"]["__tool__"]
            for src in sources
            if src["score"] >= self.retrieve_min_score
        )

        return [await self.get_tool_async(name) for name in tool_names]

    async def __call__(self, *args, **kwargs) -> list[dict]:
        tools = await self.retrieve_tools_async(*args, **kwargs)
        return [{"name": t.name, "description": t.description} for t in tools]

    class _ToolSchema(BaseModel):
        query: str = Field(description="The task to find the best tool for")

    def to_tool(self) -> Tool:
        """Convert the retriever to a tool."""

        async def _func(query: str) -> str:
            """Use this tool to retrieve the best tools for a given task"""
            # Use __call__ to get tool metadata (name and description) instead of
            # the full BaseTool objects, which can cause infinite recursion when
            # converting to string due to circular references in Pydantic models
            return json.dumps(await self.__call__(query))

        return self.tool_backend.create_tool(_func)
