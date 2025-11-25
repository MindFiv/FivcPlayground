from strands.models import Model

from fivcplayground.models.types.base import ModelConfig


def create_model(model_config: ModelConfig) -> Model:
    """Create a model instance from a ModelConfig.

    Args:
        model_config: ModelConfig instance

    Returns:
        Model instance
    """
    if model_config.provider == "openai":
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            client_args={
                "api_key": model_config.api_key,
                "base_url": model_config.base_url,
            },
            model_id=model_config.model,
            params={
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature,
            },
        )
    elif model_config.provider == "ollama":
        from strands.models.ollama import OllamaModel

        return OllamaModel(
            model_config.base_url,
            model_id=model_config.model,
            temperature=model_config.temperature,
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_config.provider}")
