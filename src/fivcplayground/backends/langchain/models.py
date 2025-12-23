from typing import Any

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from fivcplayground.models.types import (
    Model,
    ModelBackend,
    ModelConfig,
)


class LangchainModel(Model):
    def __init__(self, model: Any):
        self._model = model

    def get_underlying(self) -> Any:
        return self._model


class LangchainModelBackend(ModelBackend):
    def create_model(self, model_config: ModelConfig) -> Model:
        if model_config.provider == "openai":
            return LangchainModel(
                ChatOpenAI(
                    model=model_config.model,
                    api_key=model_config.api_key,
                    base_url=model_config.base_url,
                    temperature=model_config.temperature,
                    max_tokens=model_config.max_tokens,
                )
            )
        elif model_config.provider == "ollama":
            return LangchainModel(
                ChatOllama(
                    model=model_config.model,
                    base_url=model_config.base_url,
                    temperature=model_config.temperature,
                    reasoning=False,
                )
            )
        else:
            raise ValueError(f"Unsupported model provider: {model_config.provider}")
