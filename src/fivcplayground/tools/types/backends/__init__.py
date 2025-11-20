__all__ = [
    "make_tool",
    "get_tool_name",
    "get_tool_description",
    "set_tool_description",
    "Tool",
    "FuncTool",
    "ToolBundle",
]

from fivcplayground import __backend__

if __backend__ == "langchain":
    from .langchain import (
        make_tool,
        get_tool_name,
        get_tool_description,
        set_tool_description,
        Tool,
        FuncTool,
        ToolBundle,
    )

elif __backend__ == "strands":
    from .strands import (
        make_tool,
        get_tool_name,
        get_tool_description,
        set_tool_description,
        Tool,
        FuncTool,
        ToolBundle,
    )
