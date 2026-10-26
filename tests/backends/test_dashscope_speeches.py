"""Unit tests for DashScope speech backend and Pipecat adapters."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pipecat.frames.frames import ErrorFrame, TranscriptionFrame, TTSAudioRawFrame
from pipecat.services.tts_service import TextAggregationMode

from fivcplayground.backends.dashscope import (
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
    DashScopeSpeechRecognizer,
    DashScopeSpeechSynthesizer,
)
from fivcplayground.backends.dashscope.speeches import (
    _iter_pcm_frames,
    _strip_wav_header,
)
from fivcplayground.backends.pipecat.agents import (
    DEFAULT_STT_TRAILING_SILENCE_SECS,
    STTService,
    TTSService,
)
from fivcplayground.speeches import (
    SpeechRecognizeEvent,
    SpeechRecognizeOption,
    SpeechRecognizer,
    SpeechSynthesisOption,
    SpeechSynthesizer,
)


class TestDashScopeSpeechRecognizer:
    @pytest.mark.asyncio
    async def test_stream_async_yields_final_text(self):
        recognizer = DashScopeSpeechRecognizer(
            api_key="sk-test",
            model="qwen-audio-3.1-asr-flash-streaming",
        )

        class FakeRecognition:
            def __init__(self, *args, **kwargs):
                self.callback = kwargs.get("callback")
                self.frames = []

            def start(self):
                self.callback.on_open()

            def send_audio_frame(self, buffer: bytes):
                self.frames.append(buffer)

            def stop(self):
                sentence = {"text": "你好", "end_time": 1200}
                result = MagicMock()
                result.get_sentence.return_value = sentence
                with patch(
                    "fivcplayground.backends.dashscope.speeches.RecognitionResult.is_sentence_end",
                    side_effect=lambda s: isinstance(s, dict) and "end_time" in s,
                ):
                    self.callback.on_event(result)
                self.callback.on_complete()
                self.callback.on_close()

        with patch(
            "fivcplayground.backends.dashscope.speeches.Recognition",
            FakeRecognition,
        ):
            async with recognizer:
                events = [
                    event async for event in recognizer.stream_async(b"\x00\x00" * 100)
                ]

        assert any(e.type == "final" and e.text == "你好" for e in events)

    @pytest.mark.asyncio
    async def test_live_utterance_apis(self):
        recognizer = DashScopeSpeechRecognizer(api_key="sk-test")

        class FakeRecognition:
            def __init__(self, *args, **kwargs):
                self.callback = kwargs.get("callback")

            def start(self):
                self.callback.on_open()

            def send_audio_frame(self, buffer: bytes):
                if buffer:
                    sentence = {"text": "边说边识", "end_time": 800}
                    result = MagicMock()
                    result.get_sentence.return_value = sentence
                    with patch(
                        "fivcplayground.backends.dashscope.speeches.RecognitionResult.is_sentence_end",
                        return_value=True,
                    ):
                        self.callback.on_event(result)

            def stop(self):
                self.callback.on_complete()
                self.callback.on_close()

        with patch(
            "fivcplayground.backends.dashscope.speeches.Recognition",
            FakeRecognition,
        ):
            async with recognizer:
                await recognizer.begin_utterance()
                await recognizer.push_audio(b"\x00\x00" * 80)
                events = [e async for e in recognizer.end_utterance()]

        assert any(e.type == "final" and "边说边识" in e.text for e in events)

    @pytest.mark.asyncio
    async def test_partial_text_promoted_to_final_when_no_sentence_end(self):
        recognizer = DashScopeSpeechRecognizer(api_key="sk-test")

        class FakeRecognition:
            def __init__(self, *args, **kwargs):
                self.callback = kwargs.get("callback")

            def start(self):
                self.callback.on_open()

            def send_audio_frame(self, buffer: bytes):
                del buffer

            def stop(self):
                # Partial-only path: sentence dict without end_time.
                sentence = {"text": "你好呀"}
                result = MagicMock()
                result.get_sentence.return_value = sentence
                with patch(
                    "fivcplayground.backends.dashscope.speeches.RecognitionResult.is_sentence_end",
                    return_value=False,
                ):
                    self.callback.on_event(result)
                self.callback.on_close()

        with patch(
            "fivcplayground.backends.dashscope.speeches.Recognition",
            FakeRecognition,
        ):
            async with recognizer:
                events = [
                    event async for event in recognizer.stream_async(b"\x00\x00" * 40)
                ]

        assert events[-1].type == "final"
        assert events[-1].text == "你好呀"

    def test_option_defaults_to_pcm(self):
        recognizer = DashScopeSpeechRecognizer(api_key="sk-test")
        option = recognizer.get_option()
        assert option.format == "pcm"
        assert option.sample_rate == 16000

    def test_strip_wav_and_iter_frames(self):
        pcm = b"\x01\x02" * 50
        wav = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 32 + pcm
        assert _strip_wav_header(wav) == pcm
        frames = list(_iter_pcm_frames(pcm, frame_bytes=40))
        assert frames[0] == pcm[:40]


class TestDashScopeSpeechSynthesizer:
    def test_option_defaults(self):
        synthesizer = DashScopeSpeechSynthesizer(
            api_key="sk-test",
            model=DEFAULT_TTS_MODEL,
            voice=DEFAULT_TTS_VOICE,
        )
        option = synthesizer.get_option()
        assert option.voice == DEFAULT_TTS_VOICE
        assert option.format == "pcm"
        assert option.sample_rate == 24000

    @pytest.mark.asyncio
    async def test_stream_async_yields_multiple_chunks(self):
        synthesizer = DashScopeSpeechSynthesizer(
            api_key="sk-test",
            model="qwen-audio-3.1-tts-flash",
            voice="longanhuan_v3.1",
        )

        class FakeClient:
            def __init__(self, *args, **kwargs):
                self.callback = kwargs.get("callback")

            def streaming_call(self, text: str):
                del text
                self.callback.on_data(b"\x00\x01" * 5)
                self.callback.on_data(b"\x02\x03" * 5)

            def streaming_complete(self):
                self.callback.on_complete()

        with patch(
            "fivcplayground.backends.dashscope.speeches.DashScopeTTSV2Client",
            FakeClient,
        ):
            async with synthesizer:
                chunks = [chunk async for chunk in synthesizer.stream_async("hello")]

        assert chunks == [b"\x00\x01" * 5, b"\x02\x03" * 5]


class _FakeRecognizer(SpeechRecognizer):
    def __init__(self, events: list[SpeechRecognizeEvent]):
        self._events = events
        self._option = SpeechRecognizeOption(format="pcm", sample_rate=16000)
        self.entered = False

    @property
    def id(self) -> str:
        return "fake-recognizer"

    def get_option(self) -> SpeechRecognizeOption:
        return self._option

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.entered = False

    async def stream_async(self, audio):
        for event in self._events:
            yield event


class _FakeSynthesizer(SpeechSynthesizer):
    def __init__(self, chunks: list[bytes]):
        self._chunks = chunks
        self._option = SpeechSynthesisOption(
            voice="test-voice", format="pcm", sample_rate=24000
        )
        self.entered = False

    @property
    def id(self) -> str:
        return "fake-synthesizer"

    def get_option(self) -> SpeechSynthesisOption:
        return self._option

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.entered = False

    async def stream_async(self, text):
        for chunk in self._chunks:
            yield chunk


class TestSTTServiceAdapter:
    def test_defaults_trailing_silence_and_pcm_segments(self):
        recognizer = _FakeRecognizer([])
        stt = STTService(recognizer)
        assert stt._trailing_silence_secs == DEFAULT_STT_TRAILING_SILENCE_SECS
        assert stt.wants_wav_segments is False
        assert stt._live is False  # fake recognizer has no begin_utterance

    @pytest.mark.asyncio
    async def test_run_stt_yields_transcription(self):
        recognizer = _FakeRecognizer([SpeechRecognizeEvent(type="final", text="你好")])
        stt = STTService(recognizer)
        stt._init_sample_rate = 16000
        stt._user_id = "user"

        with (
            patch.object(stt, "start_processing_metrics", new_callable=AsyncMock),
            patch.object(stt, "stop_processing_metrics", new_callable=AsyncMock),
        ):
            async with recognizer:
                frames = [frame async for frame in stt.run_stt(b"fake-pcm")]

        assert len(frames) == 1
        assert isinstance(frames[0], TranscriptionFrame)
        assert frames[0].text == "你好"

    @pytest.mark.asyncio
    async def test_run_stt_yields_error_frame(self):
        recognizer = _FakeRecognizer(
            [SpeechRecognizeEvent(type="error", message="boom")]
        )
        stt = STTService(recognizer)
        stt._init_sample_rate = 16000

        with (
            patch.object(stt, "start_processing_metrics", new_callable=AsyncMock),
            patch.object(stt, "stop_processing_metrics", new_callable=AsyncMock),
        ):
            async with recognizer:
                frames = [frame async for frame in stt.run_stt(b"fake-pcm")]

        assert len(frames) == 1
        assert isinstance(frames[0], ErrorFrame)
        assert "boom" in frames[0].error


class TestTTSServiceAdapter:
    def test_defaults_to_sentence_aggregation(self):
        synthesizer = _FakeSynthesizer([])
        tts = TTSService(synthesizer)
        assert tts._text_aggregation_mode == TextAggregationMode.SENTENCE

    @pytest.mark.asyncio
    async def test_run_tts_yields_audio_frame(self):
        synthesizer = _FakeSynthesizer([b"\x00\x01" * 10])
        tts = TTSService(synthesizer)
        tts._init_sample_rate = 24000

        with (
            patch.object(tts, "start_processing_metrics", new_callable=AsyncMock),
            patch.object(tts, "stop_processing_metrics", new_callable=AsyncMock),
        ):
            async with synthesizer:
                frames = [frame async for frame in tts.run_tts("hello", "ctx-1")]

        assert len(frames) == 1
        assert isinstance(frames[0], TTSAudioRawFrame)
        assert frames[0].audio == b"\x00\x01" * 10
        assert frames[0].sample_rate == 24000
