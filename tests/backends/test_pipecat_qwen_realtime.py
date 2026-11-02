"""Qwen realtime service configuration and event translation."""

import base64

import pytest
from fivcplayground.models.types.base import ModelConfig
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.frames.frames import (
    InputAudioRawFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    LLMTextFrame,
    ProposedUserStartedSpeakingFrame,
    ProposedUserStoppedSpeakingFrame,
    TranscriptionFrame,
    TTSAudioRawFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
)
from pipecat.processors.aggregators.llm_context import LLMContext

_BASE_URL = "wss://example.test/api-ws/v1/realtime"


def _service(**kwargs):
    from fivcplayground.backends.pipecat.models.qwen_realtime import (
        QwenRealtimeLLMService,
    )

    settings = kwargs.pop(
        "settings",
        QwenRealtimeLLMService.Settings(
            model="qwen3.8-omni-flash-realtime",
            voice="Tina",
            turn_detection="server_vad",
        ),
    )
    return QwenRealtimeLLMService(
        api_key=kwargs.pop("api_key", "key"),
        base_url=kwargs.pop("base_url", _BASE_URL),
        settings=settings,
        **kwargs,
    )


class _FrameSink:
    def __init__(self) -> None:
        self.frames = []

    async def push_frame(self, frame, direction=None):
        del direction
        self.frames.append(frame)


class TestQwenRealtimeFactory:
    def test_builds_from_base_url_and_extra(self):
        from fivcplayground.backends.pipecat.models import PipecatModelBackend

        model = PipecatModelBackend().create_model(
            ModelConfig(
                id="pipecat-omni",
                provider="qwen_realtime",
                model="qwen3.8-omni-flash-realtime",
                api_key="dash-key",
                base_url=_BASE_URL,
                temperature=0.4,
                max_tokens=128,
                extra={
                    "voice": "Tina",
                    "input_transcription_model": "qwen3-asr-flash-realtime",
                    "input_sample_rate": 16000,
                    "output_sample_rate": 24000,
                },
            )
        )
        service = model.get_underlying()
        assert service.base_url == (f"{_BASE_URL}?model=qwen3.8-omni-flash-realtime")
        assert service._api_key == "dash-key"
        assert service._settings.voice == "Tina"
        assert service._settings.turn_detection == "server_vad"
        assert service._settings.temperature == 0.4
        assert service._settings.max_tokens == 128
        assert service._settings.input_transcription_model == (
            "qwen3-asr-flash-realtime"
        )
        assert service._settings.input_sample_rate == 16000
        assert service._settings.output_sample_rate == 24000
        assert service.turn_detection_enabled is True
        event = service.session_update_event()
        session = event["session"]
        assert session["audio"]["input"]["format"]["sample_rate"] == 16000
        assert session["audio"]["output"]["format"]["sample_rate"] == 24000
        assert session["instructions"] == ""
        assert session["turn_detection"]["type"] == "server_vad"
        assert session["input_audio_transcription"]["model"] == (
            "qwen3-asr-flash-realtime"
        )
        assert "tools" not in session

    def test_extra_overrides_sample_rates_and_transcription(self):
        from fivcplayground.backends.pipecat.models import PipecatModelBackend

        service = (
            PipecatModelBackend()
            .create_model(
                ModelConfig(
                    id="pipecat-omni",
                    provider="qwen_realtime",
                    model="qwen3.8-omni-flash-realtime",
                    api_key="dash-key",
                    base_url=_BASE_URL,
                    extra={
                        "voice": "Ethan",
                        "input_transcription_model": "custom-asr",
                        "input_sample_rate": 24000,
                        "output_sample_rate": 16000,
                    },
                )
            )
            .get_underlying()
        )
        session = service.session_update_event()["session"]
        assert session["voice"] == "Ethan"
        assert session["input_audio_transcription"]["model"] == "custom-asr"
        assert session["audio"]["input"]["format"]["sample_rate"] == 24000
        assert session["audio"]["output"]["format"]["sample_rate"] == 16000

    def test_missing_base_url_raises(self):
        from fivcplayground.backends.pipecat.models import PipecatModelBackend

        with pytest.raises(ValueError, match="base_url"):
            PipecatModelBackend().create_model(
                ModelConfig(
                    id="pipecat-omni",
                    provider="qwen_realtime",
                    model="qwen3.8-omni-flash-realtime",
                    api_key="dash-key",
                )
            )

    def test_false_turn_detection_is_manual(self):
        from fivcplayground.backends.pipecat.models import PipecatModelBackend

        model = PipecatModelBackend().create_model(
            ModelConfig(
                id="pipecat-omni",
                provider="qwen_realtime",
                model="qwen3.8-omni-flash-realtime",
                api_key="dash-key",
                base_url=_BASE_URL,
                extra={"turn_detection": False},
            )
        )
        service = model.get_underlying()
        assert service.turn_detection_enabled is False
        assert service.session_update_event()["session"]["turn_detection"] is None


class TestQwenRealtimeEvents:
    @pytest.mark.asyncio
    async def test_system_instruction_update_keeps_voice_and_session(self):
        service = _service()
        await service._update_settings(
            type(service._settings)(system_instruction="be brief")
        )
        assert service._settings.voice == "Tina"
        assert service._settings.system_instruction == "be brief"
        session = service.session_update_event()["session"]
        assert session["instructions"] == "be brief"
        assert session["voice"] == "Tina"
        assert session["input_audio_transcription"]["model"] == (
            "qwen3-asr-flash-realtime"
        )

    def test_session_update_includes_context_tools(self):
        service = _service()
        service._context = LLMContext(
            messages=[],
            tools=[
                FunctionSchema(
                    name="clock",
                    description="Read the clock",
                    properties={"zone": {"type": "string"}},
                    required=["zone"],
                )
            ],
        )
        tools = service.session_update_event()["session"]["tools"]
        assert tools == [
            {
                "type": "function",
                "name": "clock",
                "description": "Read the clock",
                "parameters": {
                    "type": "object",
                    "properties": {"zone": {"type": "string"}},
                    "required": ["zone"],
                },
            }
        ]

    @pytest.mark.asyncio
    async def test_server_events_become_pipeline_frames(self):
        service = _service()
        sink = _FrameSink()
        service.push_frame = sink.push_frame
        audio = base64.b64encode(b"\x01\x02").decode("ascii")

        await service.handle_server_event({"type": "input_audio_buffer.speech_started"})
        await service.handle_server_event({"type": "input_audio_buffer.speech_stopped"})
        await service.handle_server_event(
            {
                "type": "conversation.item.input_audio_transcription.completed",
                "transcript": "你好",
            }
        )
        await service.handle_server_event({"type": "response.created"})
        await service.handle_server_event(
            {"type": "response.audio_transcript.delta", "delta": "在的"}
        )
        await service.handle_server_event(
            {"type": "response.audio.delta", "delta": audio}
        )
        await service.handle_server_event({"type": "response.done"})

        assert isinstance(sink.frames[0], ProposedUserStartedSpeakingFrame)
        assert isinstance(sink.frames[1], ProposedUserStoppedSpeakingFrame)
        transcript = sink.frames[2]
        assert isinstance(transcript, TranscriptionFrame)
        assert transcript.text == "你好"
        assert isinstance(sink.frames[3], LLMFullResponseStartFrame)
        text = sink.frames[4]
        assert isinstance(text, LLMTextFrame)
        assert text.text == "在的"
        assert isinstance(sink.frames[5], TTSStartedFrame)
        spoken = sink.frames[6]
        assert isinstance(spoken, TTSAudioRawFrame)
        assert spoken.audio == b"\x01\x02"
        assert spoken.sample_rate == 24000
        assert isinstance(sink.frames[7], TTSStoppedFrame)
        assert isinstance(sink.frames[8], LLMFullResponseEndFrame)

    @pytest.mark.asyncio
    async def test_input_audio_is_resampled_before_append(self):
        service = _service()
        service._session_ready.set()
        sent = []

        async def capture(event):
            sent.append(event)

        async def resample(audio, in_rate, out_rate):
            assert in_rate == 24000
            assert out_rate == 16000
            assert audio == b"\x00\x01"
            return b"\x02\x03"

        service._send_event = capture
        service._resampler.resample = resample
        service._websocket = object()
        await service._send_user_audio(
            InputAudioRawFrame(audio=b"\x00\x01", sample_rate=24000, num_channels=1)
        )
        assert sent[0]["type"] == "input_audio_buffer.append"
        assert base64.b64decode(sent[0]["audio"]) == b"\x02\x03"
