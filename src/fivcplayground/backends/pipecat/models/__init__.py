"""Pipecat model backend implementations."""

from typing import Any

from fivcplayground.models import Model, ModelBackend, ModelConfig
from pipecat.services.ollama.llm import OLLamaLLMService
from pipecat.services.openai.llm import OpenAILLMService

from .qwen_realtime import (
    DEFAULT_INPUT_SAMPLE_RATE,
    DEFAULT_INPUT_TRANSCRIPTION_MODEL,
    DEFAULT_OUTPUT_SAMPLE_RATE,
    DEFAULT_REALTIME_VOICE,
    QwenRealtimeLLMService,
    build_realtime_websocket_url,
)

__all__ = [
    "PipecatModel",
    "PipecatModelBackend",
    "QwenRealtimeLLMService",
    "build_realtime_websocket_url",
]


class PipecatModel(Model):
    """Wrapper around a Pipecat LLM service."""

    def __init__(self, model: Any):
        self._model = model

    def get_underlying(self) -> Any:
        return self._model


def _qwen_turn_detection(value: Any) -> str | bool:
    """Map a config value onto server-owned or client-owned turns."""
    if value in (None, False):
        return False
    if isinstance(value, str) and value.lower() in {"false", "null", "none", "manual"}:
        return False
    return value


class PipecatModelBackend(ModelBackend):
    """Create Pipecat LLM services, including Qwen speech-to-speech realtime."""

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

        if model_config.provider == "qwen_realtime":
            return PipecatModel(_create_qwen_realtime(model_config))

        raise ValueError(f"Unsupported model provider: {model_config.provider}")


def _create_qwen_realtime(model_config: ModelConfig) -> QwenRealtimeLLMService:
    if not model_config.base_url:
        raise ValueError("Qwen realtime requires ModelConfig.base_url")
    extra: dict[str, Any] = dict(model_config.extra or {})
    voice = extra.pop("voice", DEFAULT_REALTIME_VOICE)
    input_transcription_model = extra.pop(
        "input_transcription_model", DEFAULT_INPUT_TRANSCRIPTION_MODEL
    )
    input_sample_rate = extra.pop("input_sample_rate", DEFAULT_INPUT_SAMPLE_RATE)
    output_sample_rate = extra.pop("output_sample_rate", DEFAULT_OUTPUT_SAMPLE_RATE)
    if "turn_detection" in extra:
        turn_detection = _qwen_turn_detection(extra.pop("turn_detection"))
    else:
        turn_detection = "server_vad"
    # Resolve the URL here so a bad base_url fails before the pipeline starts.
    build_realtime_websocket_url(
        model=model_config.model,
        base_url=model_config.base_url,
    )
    return QwenRealtimeLLMService(
        api_key=model_config.api_key or "",
        base_url=model_config.base_url,
        settings=QwenRealtimeLLMService.Settings(
            model=model_config.model,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            voice=voice,
            turn_detection=turn_detection,
            input_transcription_model=input_transcription_model,
            input_sample_rate=input_sample_rate,
            output_sample_rate=output_sample_rate,
        ),
        **extra,
    )
