"""Pipecat model backend implementations."""

from typing import Any

from fivcplayground.models import Model, ModelBackend, ModelConfig
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.services.openai.llm import OpenAILLMService


class PipecatModel(Model):
    """Wrapper around a Pipecat LLM service."""

    def __init__(self, model: Any):
        self._model = model

    def get_underlying(self) -> Any:
        return self._model


class PipecatModelBackend(ModelBackend):
    """Create the first-party Pipecat OpenAI-compatible model services."""

    def create_model(self, model_config: ModelConfig) -> Model:
        extra_settings: dict[str, Any] = {}
        if model_config.enable_thinking is not None:
            extra_settings["extra_body"] = {
                "enable_thinking": model_config.enable_thinking
            }

        if model_config.provider == "openai":
            # Custom OpenAI-compatible gateways (e.g. DashScope) reject the
            # "developer" role that Pipecat uses for system_instruction by default.
            # Pipecat 1.13 keeps this as a class attribute; constructor kwargs are
            # ignored, so assign on the instance after construction.
            openai_kwargs: dict[str, Any] = dict(model_config.extra or {})
            supports_developer_role = openai_kwargs.pop(
                "supports_developer_role",
                False if model_config.base_url else None,
            )
            service = OpenAILLMService(
                api_key=model_config.api_key,
                base_url=model_config.base_url,
                settings=OpenAILLMService.Settings(
                    model=model_config.model,
                    temperature=model_config.temperature,
                    max_completion_tokens=model_config.max_tokens,
                    extra=extra_settings,
                ),
                **openai_kwargs,
            )
            if supports_developer_role is not None:
                service.supports_developer_role = supports_developer_role
            return PipecatModel(service)

        if model_config.provider == "ollama":
            return PipecatModel(
                OLLamaLLMService(
                    settings=OLLamaLLMService.Settings(
                        model=model_config.model,
                        temperature=model_config.temperature,
                        max_completion_tokens=model_config.max_tokens,
                        extra=extra_settings,
                    ),
                    base_url=model_config.base_url or "http://localhost:11434/v1",
                    **(model_config.extra or {}),
                )
            )

        raise ValueError(f"Unsupported model provider: {model_config.provider}")
