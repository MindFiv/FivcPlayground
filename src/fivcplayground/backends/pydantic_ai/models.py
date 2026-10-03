from typing import Any

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.settings import ModelSettings

from fivcplayground.models import (
    Model,
    ModelBackend,
    ModelConfig,
)


class PydanticAIModel(Model):
    """Wrapper for a Pydantic AI model."""

    def __init__(self, model: Any):
        self._model = model

    def get_underlying(self) -> Any:
        return self._model


class PydanticAIModelBackend(ModelBackend):
    """Model backend for Pydantic AI."""

    def create_model(self, model_config: ModelConfig) -> Model:
        settings = ModelSettings()
        if model_config.temperature is not None:
            settings["temperature"] = model_config.temperature
        if model_config.max_tokens is not None:
            settings["max_tokens"] = model_config.max_tokens
        if model_config.enable_thinking is not None:
            settings["thinking"] = model_config.enable_thinking

        if model_config.provider == "openai":
            provider = OpenAIProvider(
                base_url=model_config.base_url,
                api_key=model_config.api_key,
            )
            return PydanticAIModel(
                OpenAIChatModel(
                    model_config.model,
                    provider=provider,
                    settings=settings or None,
                )
            )

        if model_config.provider == "ollama":
            provider = OllamaProvider(
                base_url=model_config.base_url,
                api_key=model_config.api_key,
            )
            return PydanticAIModel(
                OllamaModel(
                    model_config.model,
                    provider=provider,
                    settings=settings or None,
                )
            )

        raise ValueError(f"Unsupported model provider: {model_config.provider}")
