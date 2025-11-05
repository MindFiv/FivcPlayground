__all__ = [
    "create_model",
    "Model",
]

from fivcadvisor import __backend__

if __backend__ == "langchain":
    from .langchain import (
        create_model,
        Model,
    )

elif __backend__ == "strands":
    from .strands import (
        create_model,
        Model,
    )
