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

    def get_tool(self, name: str) -> Tool | None:
        tool = self.tools.get(name)
        if tool:
            return tool

        tool_config = self.tool_config_repository.get_tool_config(name)
        return (
            self.tool_backend.create_tool_bundle(tool_config) if tool_config else None
        )

    def list_tools(self) -> list[Tool]:
        tools = list(self.tools.values())
        tool_configs = self.tool_config_repository.list_tool_configs()
        tools.extend([self.tool_backend.create_tool_bundle(c) for c in tool_configs])
        return tools

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

    def index_tools(self):
        """Index all tools in the retriever."""

        # cleanup the indices
        self.tool_indices.cleanup()

        # rebuild indices
        for tool in self.list_tools():
            tool_name = tool.name
            tool_desc = tool.description
            self.tool_indices.add(
                tool_desc,
                metadata={"__tool__": tool_name},
            )

    def retrieve_tools(self, query: str, **kwargs) -> list[Tool]:
        """Retrieve tools based on a query."""
        sources = self.tool_indices.search(
            query,
            num_documents=self.retrieve_max_num,
        )

        tool_names = set(
            src["metadata"]["__tool__"]
            for src in sources
            if src["score"] >= self.retrieve_min_score
        )

        return [self.get_tool(name) for name in tool_names]

    def __call__(self, *args, **kwargs) -> list[dict]:
        tools = self.retrieve_tools(*args, **kwargs)
        return [{"name": t.name, "description": t.description} for t in tools]

    class _ToolSchema(BaseModel):
        query: str = Field(description="The task to find the best tool for")

    def to_tool(self) -> Tool:
        """Convert the retriever to a tool."""

        def _func(query: str) -> str:
            """Use this tool to retrieve the best tools for a given task"""
            # Use __call__ to get tool metadata (name and description) instead of
            # the full BaseTool objects, which can cause infinite recursion when
            # converting to string due to circular references in Pydantic models
            return str(self(query))

        return self.tool_backend.create_tool(_func)
