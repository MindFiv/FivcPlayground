from typing import Any

from google.adk.models import BaseLlm as AdkModelUnderlying, LiteLlm

from fivcplayground.models import (
    Model,
    ModelBackend,
    ModelConfig,
)


class AdkModel(Model):
    def __init__(self, model: AdkModelUnderlying):
        self._model = model

    def get_underlying(self) -> Any:
        return self._model


class AdkModelBackend(ModelBackend):
    def create_model(self, model_config: ModelConfig) -> Model:
        if model_config.provider not in (
            "openai",
            "ollama",
            "anthropic",
        ):
            raise ValueError(f"Unsupported model provider: {model_config.provider}")

        # print("----------------------llm")
        # print(model_config.model_dump_json())

        params: dict[str, Any] = {
            "max_tokens": model_config.max_tokens,
            "temperature": model_config.temperature,
            "api_base": model_config.base_url,
            "api_key": model_config.api_key,
        }
        if model_config.enable_thinking is not None:
            if model_config.provider == "openai":
                params["extra_body"] = {"enable_thinking": model_config.enable_thinking}
            elif model_config.provider == "ollama":
                params["think"] = model_config.enable_thinking

        params = {k: v for k, v in params.items() if v is not None}
        return AdkModel(
            LiteLlm(
                model=f"{model_config.provider}/{model_config.model}",
                stream=True,
                **params,
            )
        )
