from typing import Any

from strands.models.openai import OpenAIModel
from strands.models.ollama import OllamaModel

from fivcplayground.models import (
    Model,
    ModelBackend,
    ModelConfig,
)


class StrandsModel(Model):
    def __init__(self, model: Any):
        self._model = model

    def get_underlying(self) -> Any:
        return self._model


class StrandsModelBackend(ModelBackend):
    def create_model(self, model_config: ModelConfig) -> Model:
        if model_config.provider == "openai":
            return StrandsModel(
                OpenAIModel(
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
            )
        elif model_config.provider == "ollama":
            return StrandsModel(
                OllamaModel(
                    model_config.base_url,
                    model_id=model_config.model,
                    temperature=model_config.temperature,
                )
            )
        else:
            raise ValueError(f"Unsupported model provider: {model_config.provider}")
