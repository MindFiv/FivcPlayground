__all__ = [
    "AgentsRunnable",
]

from fivcadvisor import __backend__

if __backend__ == "langchain":
    from .langchain import AgentsRunnable

elif __backend__ == "strands":
    from .strands import AgentsRunnable
