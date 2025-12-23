__all__ = [
    "create_model",
    "create_chat_model",
    "create_reasoning_model",
    "create_coding_model",
    "Model",
    "ModelBackend",
    "ModelConfig",
    "ModelConfigRepository",
]

from fivcplayground.models.types import (
    Model,
    ModelBackend,
    ModelConfig,
    ModelConfigRepository,
)


def create_model(
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
        # Use file-based repository by default
        from fivcplayground.models.types.repositories.files import (
            FileModelConfigRepository,
        )

        model_config_repository = FileModelConfigRepository()

    model_config = model_config_repository.get_model_config(
        model_config_id,
    )

    if not model_config:
        if raise_exception:
            raise ValueError("Default model not found")
        return None

    return model_backend.create_model(model_config)


def create_chat_model(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model | None:
    return create_model(model_backend, model_config_repository, "chat", **kwargs)


def create_reasoning_model(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model | None:
    return create_model(model_backend, model_config_repository, "reasoning", **kwargs)


def create_coding_model(
    model_backend: ModelBackend | None = None,
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model | None:
    return create_model(model_backend, model_config_repository, "coding", **kwargs)
