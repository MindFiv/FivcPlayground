__all__ = [
    "create_model",
    "create_chat_model",
    "create_reasoning_model",
    "create_coding_model",
    "Model",
    "ModelConfig",
    "ModelConfigRepository",
]

from fivcplayground.models.types.backends import create_model as _create_model, Model
from fivcplayground.models.types.repositories import ModelConfig, ModelConfigRepository


def create_model(
    model_config_repository: ModelConfigRepository | None = None,
    model_config_id: str = "default",
    **kwargs,  # ignore additional kwargs
) -> Model:
    """Factory function to create a LLM instance."""

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
        raise ValueError("Default model not found")

    return _create_model(model_config)


def create_chat_model(
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model:
    return create_model(model_config_repository, "chat")


def create_reasoning_model(
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model:
    return create_model(model_config_repository, "reasoning")


def create_coding_model(
    model_config_repository: ModelConfigRepository | None = None,
    **kwargs,  # ignore additional kwargs
) -> Model:
    return create_model(model_config_repository, "coding")
