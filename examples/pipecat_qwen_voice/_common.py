"""Shared helpers for the Qwen local-audio Pipecat example and e2e test."""

from __future__ import annotations

import os
from typing import Any

from fivcplayground.agents import AgentConfig
from fivcplayground.backends.dashscope import (
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
    DashScopeSpeechRecognizer,
    DashScopeSpeechSynthesizer,
    configure_dashscope_websocket_url,
)
from fivcplayground.backends.pipecat.agents import (
    DEFAULT_STT_TRAILING_SILENCE_SECS,
    PipecatAgentRunnable,
)
from fivcplayground.backends.pipecat.models import PipecatModelBackend
from fivcplayground.backends.pipecat.tools import PipecatToolBackend
from fivcplayground.models import ModelConfig
from fivcplayground.speeches import SpeechRecognizeOption, SpeechSynthesisOption
from fivcplayground.tools import (
    ToolConfig,
    ToolRetriever,
    create_builtin_tools_async,
)
from fivcplayground.tools.types.repositories.base import ToolConfigRepository

DASHSCOPE_COMPAT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_LLM_MODEL = "deepseek-v4.1-flash"
DEFAULT_IDLE_TIMEOUT_SECS = 120
DEFAULT_VAD_STOP_SECS = 0.2
BUILTIN_TOOL_IDS = ["auxiliary", "filesystem", "shell"]


class _EmptyToolConfigRepository(ToolConfigRepository):
    """No MCP/config tools; builtins are passed directly into ToolRetriever."""

    async def update_tool_config_async(self, tool_config: ToolConfig) -> None:
        del tool_config

    async def get_tool_config_async(self, tool_id: str) -> ToolConfig | None:
        del tool_id
        return None

    async def list_tool_configs_async(self, **kwargs) -> list[ToolConfig]:
        del kwargs
        return []

    async def delete_tool_config_async(self, tool_id: str) -> None:
        del tool_id


class _NoopToolIndices:
    def cleanup(self) -> None:
        return None

    def add(self, *args, **kwargs) -> None:
        del args, kwargs

    def search(self, *args, **kwargs) -> list:
        del args, kwargs
        return []


class _NoopEmbeddingDB:
    """Satisfies ToolRetriever's embedding_db assert without Chroma."""

    def __init__(self) -> None:
        self.tools = _NoopToolIndices()


def require_dashscope_api_key() -> str:
    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY is required for Qwen Audio STT/TTS and the LLM."
        )
    return api_key


def _optional_device_index(env_name: str) -> int | None:
    raw = os.environ.get(env_name, "").strip()
    if not raw:
        return None
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    return float(raw)


def stt_trailing_silence_secs() -> float:
    return _env_float("PIPECAT_STT_TRAILING_SILENCE", DEFAULT_STT_TRAILING_SILENCE_SECS)


def build_local_transport():
    """Create a LocalAudioTransport for default (or env-selected) devices."""
    from pipecat.transports.local.audio import (
        LocalAudioTransport,
        LocalAudioTransportParams,
    )

    return LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            input_device_index=_optional_device_index("PIPECAT_AUDIO_IN_DEVICE"),
            output_device_index=_optional_device_index("PIPECAT_AUDIO_OUT_DEVICE"),
        )
    )


def build_vad():
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.audio.vad.vad_analyzer import VADParams

    stop_secs = _env_float("PIPECAT_VAD_STOP_SECS", DEFAULT_VAD_STOP_SECS)
    return SileroVADAnalyzer(params=VADParams(stop_secs=stop_secs))


def build_stt(api_key: str) -> DashScopeSpeechRecognizer:
    return DashScopeSpeechRecognizer(
        api_key=api_key,
        model=os.environ.get("PIPECAT_QWEN_STT_MODEL", DEFAULT_STT_MODEL),
        option=SpeechRecognizeOption(format="pcm", sample_rate=16000),
    )


def build_tts(api_key: str) -> DashScopeSpeechSynthesizer:
    return DashScopeSpeechSynthesizer(
        api_key=api_key,
        model=os.environ.get("PIPECAT_QWEN_TTS_MODEL", DEFAULT_TTS_MODEL),
        option=SpeechSynthesisOption(
            voice=os.environ.get("PIPECAT_QWEN_TTS_VOICE", DEFAULT_TTS_VOICE),
            format="pcm",
            sample_rate=24000,
        ),
    )


async def build_tool_retriever() -> ToolRetriever:
    """Builtin tools only; no Chroma / embedding index required."""
    backend = PipecatToolBackend()
    tools = await create_builtin_tools_async(tool_backend=backend)
    return ToolRetriever(
        tool_backend=backend,
        tools=tools,
        tool_config_repository=_EmptyToolConfigRepository(),
        embedding_db=_NoopEmbeddingDB(),
    )


async def warmup_voice_stack(
    stt: DashScopeSpeechRecognizer,
    tts: DashScopeSpeechSynthesizer,
    llm: Any | None = None,
) -> None:
    """Prime DashScope STT/TTS (and optionally LLM) before the first user turn."""
    # ~100ms of silence at 16 kHz 16-bit mono.
    silence = b"\x00\x00" * 1600
    async with stt:
        async for _ in stt.stream_async(silence):
            pass
    async with tts:
        async for _ in tts.stream_async("嗯"):
            pass
    if llm is not None and getattr(llm, "_client", None) is not None:
        model_name = getattr(getattr(llm, "_settings", None), "model", None)
        if model_name:
            await llm._client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1,
            )


def build_voice_agent(
    *,
    idle_timeout_secs: int = DEFAULT_IDLE_TIMEOUT_SECS,
    system_prompt: str | None = None,
) -> PipecatAgentRunnable:
    api_key = require_dashscope_api_key()
    configure_dashscope_websocket_url()

    model = PipecatModelBackend().create_model(
        ModelConfig(
            id="qwen-voice-llm",
            provider="openai",
            model=os.environ.get("PIPECAT_QWEN_LLM_MODEL", DEFAULT_LLM_MODEL),
            api_key=api_key,
            base_url=os.environ.get(
                "PIPECAT_QWEN_LLM_BASE_URL", DASHSCOPE_COMPAT_BASE_URL
            ),
        )
    )
    prompt = system_prompt or (
        "You are a helpful voice assistant. Use tools when they help answer "
        "(clock, calculator, filesystem, shell). Keep spoken replies short "
        "(one or two sentences)."
    )
    return PipecatAgentRunnable(
        AgentConfig(
            id="qwen-voice",
            system_prompt=prompt,
            extra={
                "idle_timeout_secs": idle_timeout_secs,
                "pipeline_params": {"enable_metrics": True},
            },
        ),
        model.get_underlying(),
    )


def build_voice_stack(
    *,
    idle_timeout_secs: int = DEFAULT_IDLE_TIMEOUT_SECS,
) -> dict[str, Any]:
    """Assemble transport, VAD, STT, TTS, and agent for a local voice session."""
    api_key = require_dashscope_api_key()
    configure_dashscope_websocket_url()
    return {
        "agent": build_voice_agent(idle_timeout_secs=idle_timeout_secs),
        "transport": build_local_transport(),
        "vad": build_vad(),
        "stt": build_stt(api_key),
        "tts": build_tts(api_key),
    }
