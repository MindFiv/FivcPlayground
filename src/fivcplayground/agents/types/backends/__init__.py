__all__ = [
    "AgentRunnable",
]

from fivcplayground import __backend__

if __backend__ == "langchain":
    from .langchain import AgentRunnable

elif __backend__ == "strands":
    from .strands import AgentRunnable
