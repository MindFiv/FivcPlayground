"""Qwen-Omni realtime speech-to-speech service for Pipecat."""

from __future__ import annotations

import asyncio
import base64
import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from loguru import logger
from websockets.asyncio.client import connect as websocket_connect

from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.utils import create_stream_resampler
from pipecat.frames.frames import (
    Frame,
    FunctionCallCancelFrame,
    FunctionCallFromLLM,
    FunctionCallResultFrame,
    InputAudioRawFrame,
    InterruptionFrame,
    LLMContextFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMServiceMetadataFrame,
    LLMSetToolsFrame,
    LLMTextFrame,
    ProposedUserStartedSpeakingFrame,
    ProposedUserStoppedSpeakingFrame,
    TranscriptionFrame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    UserAudioRawFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.frame_processor import FrameDirection
from pipecat.services.llm_service import LLMService
from pipecat.services.settings import LLMSettings
from pipecat.turns.user_turn_strategies import ExternalUserTurnStrategies
from pipecat.utils.time import time_now_iso8601
from pipecat.utils.types import NOT_GIVEN, NotGiven, is_given

DEFAULT_REALTIME_MODEL = "qwen3.8-omni-flash-realtime"
DEFAULT_REALTIME_VOICE = "Tina"
DEFAULT_INPUT_TRANSCRIPTION_MODEL = "qwen3-asr-flash-realtime"
DEFAULT_INPUT_SAMPLE_RATE = 16000
DEFAULT_OUTPUT_SAMPLE_RATE = 24000


def build_realtime_websocket_url(*, model: str, base_url: str) -> str:
    """Validate ``base_url`` and ensure the ``model`` query parameter is set."""
    if not base_url:
        raise ValueError("Qwen realtime requires base_url")
    parts = urlsplit(base_url)
    if parts.scheme not in {"ws", "wss"}:
        raise ValueError("Qwen realtime base_url must be a ws:// or wss:// URL")
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["model"] = model
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


@dataclass
class QwenRealtimeLLMSettings(LLMSettings):
    """Runtime settings for a Qwen realtime session.

    ``turn_detection`` is ``"server_vad"`` or ``"semantic_vad"`` when the
    service owns turns, and ``False`` when the client commits each turn.
    """

    voice: str | None | NotGiven = field(default_factory=lambda: NOT_GIVEN)
    turn_detection: str | bool | None | NotGiven = field(
        default_factory=lambda: NOT_GIVEN
    )
    input_transcription_model: str | None | NotGiven = field(
        default_factory=lambda: NOT_GIVEN
    )
    input_sample_rate: int | None | NotGiven = field(default_factory=lambda: NOT_GIVEN)
    output_sample_rate: int | None | NotGiven = field(default_factory=lambda: NOT_GIVEN)


def _store_settings(
    settings: QwenRealtimeLLMSettings | None,
) -> QwenRealtimeLLMSettings:
    """Fill a store-mode settings object, then apply any provided delta."""
    store = QwenRealtimeLLMSettings(
        model=DEFAULT_REALTIME_MODEL,
        system_instruction=None,
        temperature=None,
        max_tokens=None,
        top_p=None,
        top_k=None,
        frequency_penalty=None,
        presence_penalty=None,
        seed=None,
        filter_incomplete_user_turns=False,
        user_turn_completion_config=None,
        use_provider_thinking_default=False,
        voice=DEFAULT_REALTIME_VOICE,
        turn_detection="server_vad",
        input_transcription_model=DEFAULT_INPUT_TRANSCRIPTION_MODEL,
        input_sample_rate=DEFAULT_INPUT_SAMPLE_RATE,
        output_sample_rate=DEFAULT_OUTPUT_SAMPLE_RATE,
    )
    if settings is not None:
        store.apply_update(settings)
    return store


class QwenRealtimeLLMService(LLMService):
    """Full-duplex Qwen-Omni session over the Realtime WebSocket.

    The service consumes microphone PCM and emits speech audio itself.
    Leave the pipeline's separate STT and TTS services unset. With the
    default ``server_vad`` turn detection, also leave local VAD unset so
    only one side proposes user turns.
    """

    Settings = QwenRealtimeLLMSettings
    _settings: Settings

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        settings: QwenRealtimeLLMSettings | None = None,
        **kwargs: Any,
    ) -> None:
        if not api_key:
            raise ValueError("Qwen realtime requires api_key")
        if not base_url:
            raise ValueError("Qwen realtime requires base_url")
        super().__init__(settings=_store_settings(settings), **kwargs)
        self._api_key = api_key
        self._base_url = base_url
        self._websocket: Any = None
        self._receive_task: asyncio.Task | None = None
        self._disconnecting = False
        self._session_ready = asyncio.Event()
        self._pending_audio = bytearray()
        self._context: LLMContext | None = None
        self._user_id = ""
        self._response_open = False
        self._audio_started = False
        self._open_function_calls: set[str] = set()
        self._resampler = create_stream_resampler()

    @property
    def base_url(self) -> str:
        """WebSocket URL for the current model."""
        model = self._settings.model or DEFAULT_REALTIME_MODEL
        return build_realtime_websocket_url(model=model, base_url=self._base_url)

    @property
    def turn_detection_enabled(self) -> bool:
        """Whether the server, not the client, decides when a user turn ends."""
        return self._settings.turn_detection not in (False, None)

    @property
    def input_sample_rate(self) -> int:
        return self._settings.input_sample_rate or DEFAULT_INPUT_SAMPLE_RATE

    @property
    def output_sample_rate(self) -> int:
        return self._settings.output_sample_rate or DEFAULT_OUTPUT_SAMPLE_RATE

    def service_metadata_frame(self) -> LLMServiceMetadataFrame:
        """Mark this service as realtime and recommend external turn strategies."""
        emits_turn_frames = self.turn_detection_enabled
        self._warn_if_realtime_service_emits_no_turn_frames(emits_turn_frames)
        return LLMServiceMetadataFrame(
            service_name=self.name,
            is_realtime_service=True,
            user_turn_strategies=(
                ExternalUserTurnStrategies() if emits_turn_frames else None
            ),
        )

    def session_update_event(self) -> dict[str, Any]:
        """Build the ``session.update`` event for the current settings and tools."""
        voice = self._settings.voice or DEFAULT_REALTIME_VOICE
        transcription_model = (
            self._settings.input_transcription_model
            or DEFAULT_INPUT_TRANSCRIPTION_MODEL
        )
        session: dict[str, Any] = {
            "modalities": ["text", "audio"],
            "instructions": self._settings.system_instruction or "",
            "voice": voice,
            "audio": {
                "input": {
                    "format": {
                        "type": "pcm",
                        "sample_rate": self.input_sample_rate,
                        "sample_format": "s16le",
                        "channels": 1,
                    }
                },
                "output": {
                    "voice": voice,
                    "format": {
                        "type": "pcm",
                        "sample_rate": self.output_sample_rate,
                    },
                },
            },
            "input_audio_transcription": {"model": transcription_model},
            "turn_detection": self._turn_detection_payload(),
        }
        if self._settings.temperature is not None:
            session["temperature"] = self._settings.temperature
        if self._settings.max_tokens is not None:
            session["max_tokens"] = self._settings.max_tokens
        tools = self._tool_definitions()
        if tools:
            session["tools"] = tools
        return {
            "type": "session.update",
            "event_id": self._event_id(),
            "session": session,
        }

    async def start(self, frame: Frame) -> None:
        await super().start(frame)
        await self._connect()

    async def stop(self, frame: Frame) -> None:
        await super().stop(frame)
        await self._disconnect()

    async def cancel(self, frame: Frame) -> None:
        await super().cancel(frame)
        await self._disconnect()

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMContextFrame):
            self._context = frame.context
            await self._send_session_update()
        elif isinstance(frame, LLMSetToolsFrame):
            self._sync_registered_tool_handlers(frame.tools)
            await self._send_session_update()
        elif isinstance(frame, InputAudioRawFrame):
            if isinstance(frame, UserAudioRawFrame) and frame.user_id:
                self._user_id = frame.user_id
            await self._send_user_audio(frame)
        elif isinstance(frame, InterruptionFrame):
            await self._cancel_response()
        elif isinstance(frame, UserStoppedSpeakingFrame):
            if not self.turn_detection_enabled:
                await self._send_event({"type": "input_audio_buffer.commit"})
                await self._send_event({"type": "response.create"})

        await self.push_frame(frame, direction)

    async def push_frame(
        self,
        frame: Frame,
        direction: FrameDirection = FrameDirection.DOWNSTREAM,
    ) -> None:
        if direction == FrameDirection.DOWNSTREAM:
            if isinstance(frame, FunctionCallResultFrame):
                await self._send_function_result(frame)
            elif isinstance(frame, FunctionCallCancelFrame):
                await self._send_function_result_text(frame.tool_call_id, "CANCELLED")
                await self._send_event({"type": "response.create"})
        await super().push_frame(frame, direction)

    async def _update_settings(self, delta: LLMSettings) -> dict[str, Any]:
        changed = await super()._update_settings(delta)
        if self._websocket and changed.keys() & {
            "system_instruction",
            "voice",
            "turn_detection",
            "input_transcription_model",
            "input_sample_rate",
            "output_sample_rate",
            "temperature",
            "max_tokens",
            "model",
        }:
            await self._send_session_update()
        return changed

    async def handle_server_event(self, event: dict[str, Any]) -> None:
        """Translate one Qwen realtime server event into pipeline frames."""
        event_type = event.get("type")
        if event_type == "session.created":
            await self._send_session_update()
        elif event_type == "session.updated":
            await self._mark_session_ready()
        elif event_type == "input_audio_buffer.speech_started":
            await self.push_frame(ProposedUserStartedSpeakingFrame())
            await self._cancel_response()
        elif event_type == "input_audio_buffer.speech_stopped":
            await self.push_frame(ProposedUserStoppedSpeakingFrame())
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = (event.get("transcript") or "").strip()
            if transcript:
                await self.push_frame(
                    TranscriptionFrame(transcript, self._user_id, time_now_iso8601())
                )
        elif event_type == "response.created":
            self._response_open = True
            self._audio_started = False
            await self.push_frame(LLMFullResponseStartFrame())
        elif event_type == "response.audio_transcript.delta":
            delta = event.get("delta") or ""
            if delta:
                await self.push_frame(LLMTextFrame(delta))
        elif event_type == "response.audio.delta":
            await self._push_audio_delta(event.get("delta") or "")
        elif event_type == "response.done":
            await self._finish_response()
        elif event_type == "response.function_call_arguments.done":
            await self._start_function_call(event)
        elif event_type == "error":
            message = event.get("error") or event
            await self.push_error(error_msg=f"Qwen realtime error: {message}")
        else:
            logger.trace(f"{self}: ignoring realtime event {event_type}")

    async def _connect(self) -> None:
        if self._websocket is not None:
            return
        self._disconnecting = False
        self._session_ready.clear()
        try:
            self._websocket = await websocket_connect(
                uri=self.base_url,
                additional_headers={"Authorization": f"Bearer {self._api_key}"},
            )
            self._receive_task = self.create_task(self._receive_loop())
        except Exception as exc:
            self._websocket = None
            await self.push_error(
                error_msg=f"Qwen realtime connection failed: {exc}",
                exception=exc,
            )

    async def _disconnect(self) -> None:
        self._disconnecting = True
        self._session_ready.clear()
        websocket = self._websocket
        self._websocket = None
        if websocket is not None:
            try:
                await websocket.close()
            except Exception as exc:
                logger.debug(f"{self}: websocket close failed: {exc}")
        if self._receive_task is not None:
            await self.cancel_task(self._receive_task, timeout=1.0)
            self._receive_task = None
        self._pending_audio.clear()
        self._open_function_calls.clear()
        self._response_open = False
        self._audio_started = False
        self._disconnecting = False

    async def _receive_loop(self) -> None:
        websocket = self._websocket
        if websocket is None:
            return
        try:
            async for raw in websocket:
                if isinstance(raw, bytes):
                    raw = raw.decode()
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError as exc:
                    await self.push_error(
                        error_msg=f"Invalid Qwen realtime event: {exc}",
                        exception=exc,
                    )
                    continue
                if isinstance(event, dict):
                    await self.handle_server_event(event)
        except Exception as exc:
            if not self._disconnecting:
                await self.push_error(
                    error_msg=f"Qwen realtime receive failed: {exc}",
                    exception=exc,
                )

    async def _send_session_update(self) -> None:
        if self._websocket is None:
            return
        await self._send_event(self.session_update_event())

    async def _send_user_audio(self, frame: InputAudioRawFrame) -> None:
        audio = frame.audio
        if not audio:
            return
        target_rate = self.input_sample_rate
        if frame.sample_rate != target_rate:
            audio = await self._resampler.resample(
                audio, frame.sample_rate, target_rate
            )
        if not audio:
            return
        if not self._session_ready.is_set():
            self._pending_audio.extend(audio)
            return
        await self._append_audio(audio)

    async def _mark_session_ready(self) -> None:
        self._session_ready.set()
        if not self._pending_audio:
            return
        pending = bytes(self._pending_audio)
        self._pending_audio.clear()
        await self._append_audio(pending)

    async def _append_audio(self, audio: bytes) -> None:
        await self._send_event(
            {
                "type": "input_audio_buffer.append",
                "audio": base64.b64encode(audio).decode("ascii"),
            }
        )

    async def _cancel_response(self) -> None:
        if not self._response_open:
            return
        await self._send_event({"type": "response.cancel"})

    async def _push_audio_delta(self, delta: str) -> None:
        if not delta:
            return
        if not self._audio_started:
            self._audio_started = True
            await self.push_frame(TTSStartedFrame())
        await self.push_frame(
            TTSAudioRawFrame(
                audio=base64.b64decode(delta),
                sample_rate=self.output_sample_rate,
                num_channels=1,
            )
        )

    async def _finish_response(self) -> None:
        if self._audio_started:
            self._audio_started = False
            await self.push_frame(TTSStoppedFrame())
        if self._response_open:
            self._response_open = False
            await self.push_frame(LLMFullResponseEndFrame())

    async def _start_function_call(self, event: dict[str, Any]) -> None:
        call_id = str(event.get("call_id") or event.get("item_id") or "")
        name = str(event.get("name") or "")
        if not call_id or not name:
            await self.push_error(
                error_msg="Qwen realtime function call is missing call_id or name"
            )
            return
        raw_arguments = event.get("arguments") or {}
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments) if raw_arguments else {}
            except json.JSONDecodeError as exc:
                await self.push_error(
                    error_msg=f"Invalid function call arguments: {exc}",
                    exception=exc,
                )
                return
        elif isinstance(raw_arguments, dict):
            arguments = raw_arguments
        else:
            arguments = {}
        self._open_function_calls.add(call_id)
        await self.run_function_calls(
            [
                FunctionCallFromLLM(
                    function_name=name,
                    tool_call_id=call_id,
                    arguments=arguments,
                    context=self._context,
                )
            ]
        )

    async def _send_function_result(self, frame: FunctionCallResultFrame) -> None:
        if isinstance(frame.result, str):
            output = frame.result
        elif frame.result is None:
            output = ""
        else:
            output = json.dumps(frame.result, ensure_ascii=False)
        await self._send_function_result_text(frame.tool_call_id, output)
        await self._send_event({"type": "response.create"})

    async def _send_function_result_text(self, tool_call_id: str, output: str) -> None:
        if tool_call_id not in self._open_function_calls:
            return
        self._open_function_calls.discard(tool_call_id)
        await self._send_event(
            {
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": tool_call_id,
                    "output": output,
                },
            }
        )

    async def _send_event(self, event: dict[str, Any]) -> None:
        websocket = self._websocket
        if websocket is None or self._disconnecting:
            return
        payload = dict(event)
        payload.setdefault("event_id", self._event_id())
        try:
            await websocket.send(json.dumps(payload))
        except Exception as exc:
            if self._disconnecting or self._websocket is None:
                return
            await self.push_error(
                error_msg=f"Qwen realtime send failed: {exc}",
                exception=exc,
            )

    def _turn_detection_payload(self) -> dict[str, Any] | None:
        mode = self._settings.turn_detection
        if mode in (False, None):
            return None
        turn_type = mode if isinstance(mode, str) else "server_vad"
        return {
            "type": turn_type,
            "threshold": 0.5,
            "prefix_padding_ms": 500,
            "silence_duration_ms": 800,
        }

    def _tool_definitions(self) -> list[dict[str, Any]]:
        if self._context is None or not is_given(self._context.tools):
            return []
        tools = self._context.tools
        if isinstance(tools, ToolsSchema):
            schemas = list(tools.standard_tools)
        else:
            return []
        definitions: list[dict[str, Any]] = []
        for schema in schemas:
            spec = schema.to_default_dict()
            definitions.append({"type": "function", **spec})
        return definitions

    @staticmethod
    def _event_id() -> str:
        return f"event_{uuid4().hex}"
