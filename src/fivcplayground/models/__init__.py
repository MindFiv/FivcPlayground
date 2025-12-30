__all__ = [
    "create_model",
    "create_model_async",
    "Model",
    "ModelBackend",
    "ModelConfig",
    "ModelConfigRepository",
]

from typing_extensions import deprecated

from fivcplayground.models.types import (
    Model,
    ModelBackend,
    ModelConfig,
    ModelConfigRepository,
)


@deprecated("Use create_model_async instead")
def create_model(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    model_config_id: str = "default",
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> Model | None:
    """Factory function to create a LLM instance."""
    import asyncio

    return asyncio.run(
        create_model_async(
            model_backend=model_backend,
            model_config_repository=model_config_repository,
            model_config_id=model_config_id,
            raise_exception=raise_exception,
            **kwargs,
        )
    )


async def create_model_async(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    model_config_id: str = "default",
    raise_exception: bool = True,
    **kwargs,  # ignore additional kwargs
) -> Model | None:
    """Factory function to create a LLM instance."""
    if not model_backend:
        if raise_exception:
            raise RuntimeError("No model backend specified")

        return None

    if not model_config_repository:
        if raise_exception:
            raise RuntimeError("No model config repository specified")

        return None

    model_config = await model_config_repository.get_model_config_async(
        model_config_id,
    )

    if not model_config:
        if raise_exception:
            raise ValueError("Default model not found")
        return None

    return model_backend.create_model(model_config)


@deprecated("Use create_model(model_config_id='chat') instead")
def create_chat_model(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model | None:
    return create_model(model_backend, model_config_repository, "chat", **kwargs)


@deprecated("Use create_model(model_config_id='reasoning') instead")
def create_reasoning_model(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model | None:
    return create_model(model_backend, model_config_repository, "reasoning", **kwargs)


@deprecated("Use create_model(model_config_id='coding') instead")
def create_coding_model(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model | None:
    return create_model(model_backend, model_config_repository, "coding", **kwargs)
