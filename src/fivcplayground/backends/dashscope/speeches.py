"""DashScope implementations of SpeechRecognizer and SpeechSynthesizer."""

from __future__ import annotations

import asyncio
import os
import queue
import threading
from collections.abc import AsyncIterator
from typing import Self
from uuid import uuid4

import dashscope
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult
from dashscope.audio.tts_v2 import AudioFormat as TTSV2AudioFormat
from dashscope.audio.tts_v2 import ResultCallback
from dashscope.audio.tts_v2 import SpeechSynthesizer as DashScopeTTSV2Client
from loguru import logger

from fivcplayground.speeches import (
    SpeechError,
    SpeechRecognizeEvent,
    SpeechRecognizeOption,
    SpeechRecognizer,
    SpeechSynthesisOption,
    SpeechSynthesizer,
)

DEFAULT_STT_MODEL = "qwen-audio-3.1-asr-flash-streaming"
DEFAULT_TTS_MODEL = "qwen-audio-3.1-tts-flash"
DEFAULT_TTS_VOICE = "longanhuan_v3.1"
# 100ms of 16-bit mono PCM at 16 kHz.
_DEFAULT_PCM_FRAME_BYTES = 3200


def _resolve_api_key(api_key: str | None) -> str:
    resolved = api_key or os.getenv("DASHSCOPE_API_KEY")
    if not resolved:
        raise ValueError(
            "DashScope API key is required. Pass api_key=... or set DASHSCOPE_API_KEY."
        )
    return resolved


def configure_dashscope_websocket_url(url: str | None = None) -> None:
    """Optionally point DashScope audio WebSocket at a workspace endpoint."""
    resolved = (url or os.getenv("DASHSCOPE_BASE_WEBSOCKET_API_URL") or "").strip()
    if resolved:
        dashscope.base_websocket_api_url = resolved


def _strip_wav_header(payload: bytes) -> bytes:
    if len(payload) >= 44 and payload[:4] == b"RIFF" and payload[8:12] == b"WAVE":
        return payload[44:]
    return payload


def _extract_recognition_text(result: RecognitionResult) -> str:
    sentence = result.get_sentence()
    if isinstance(sentence, dict):
        return sentence.get("text", "") or ""
    if isinstance(sentence, list):
        return " ".join(item.get("text", "") for item in sentence if item.get("text"))
    return ""


def _iter_pcm_frames(payload: bytes, frame_bytes: int = _DEFAULT_PCM_FRAME_BYTES):
    data = _strip_wav_header(payload)
    if not data:
        return
    for offset in range(0, len(data), frame_bytes):
        yield data[offset : offset + frame_bytes]


class DashScopeSpeechRecognizer(SpeechRecognizer):
    """DashScope streaming ASR via ``Recognition.send_audio_frame``.

    Supports live utterances (``begin_utterance`` / ``push_audio`` /
    ``end_utterance``) so Pipecat can open the ASR websocket while the user
    is still speaking, then finalize on VAD stop.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_STT_MODEL,
        option: SpeechRecognizeOption | None = None,
    ) -> None:
        self._id = str(uuid4())
        self._api_key = _resolve_api_key(api_key)
        self._model = model
        self._option = option or SpeechRecognizeOption(
            format="pcm",
            sample_rate=16000,
        )
        self._entered = False
        self._utt_audio_queue: queue.Queue[bytes | None] | None = None
        self._utt_event_queue: (
            asyncio.Queue[SpeechRecognizeEvent | None | BaseException] | None
        ) = None
        self._utt_worker: threading.Thread | None = None
        self._utt_last_text = ""
        self._utt_opened = threading.Event()

    @property
    def id(self) -> str:
        return self._id

    def get_option(self) -> SpeechRecognizeOption:
        return self._option

    async def __aenter__(self) -> Self:
        dashscope.api_key = self._api_key
        self._entered = True
        return self

    async def __aexit__(self, *exc: object) -> None:
        if self._utt_worker is not None:
            await self.cancel_utterance()
        self._entered = False

    def _require_entered(self) -> None:
        if not self._entered:
            raise SpeechError(
                f"{type(self).__name__} must be entered before recognition"
            )

    async def begin_utterance(self) -> None:
        """Open a DashScope ASR session (call when the user starts speaking)."""
        self._require_entered()
        if self._utt_worker is not None:
            await self.cancel_utterance()

        loop = asyncio.get_running_loop()
        event_queue: asyncio.Queue[SpeechRecognizeEvent | None | BaseException] = (
            asyncio.Queue()
        )
        audio_queue: queue.Queue[bytes | None] = queue.Queue()
        opened = threading.Event()
        last_text_box = {"text": ""}
        closed = {"done": False}

        class _Callback(RecognitionCallback):
            def on_open(self) -> None:
                opened.set()

            def on_event(self, result: RecognitionResult) -> None:
                sentence = result.get_sentence()
                text = _extract_recognition_text(result).strip()
                if not text:
                    return
                last_text_box["text"] = text
                is_final = isinstance(sentence, dict) and bool(
                    RecognitionResult.is_sentence_end(sentence)
                )
                event = SpeechRecognizeEvent(
                    type="final" if is_final else "partial",
                    text=text,
                )
                loop.call_soon_threadsafe(event_queue.put_nowait, event)

            def on_error(self, result: RecognitionResult) -> None:
                loop.call_soon_threadsafe(
                    event_queue.put_nowait,
                    SpeechRecognizeEvent(type="error", message=str(result)),
                )
                loop.call_soon_threadsafe(event_queue.put_nowait, None)

            def on_complete(self) -> None:
                loop.call_soon_threadsafe(event_queue.put_nowait, None)

            def on_close(self) -> None:
                if not closed["done"]:
                    closed["done"] = True
                    loop.call_soon_threadsafe(event_queue.put_nowait, None)

        def _worker() -> None:
            try:
                recognition = Recognition(
                    model=self._model,
                    callback=_Callback(),
                    format=self._option.format,
                    sample_rate=self._option.sample_rate,
                    api_key=self._api_key,
                )
                recognition.start()
                if not opened.wait(timeout=10):
                    raise TimeoutError("DashScope ASR websocket open timed out")
                try:
                    while True:
                        frame = audio_queue.get()
                        if frame is None:
                            break
                        recognition.send_audio_frame(frame)
                finally:
                    recognition.stop()
            except BaseException as exc:  # noqa: BLE001 - bridge to async consumer
                loop.call_soon_threadsafe(event_queue.put_nowait, exc)
                loop.call_soon_threadsafe(event_queue.put_nowait, None)

        worker = threading.Thread(target=_worker, name="dashscope-asr", daemon=True)
        self._utt_audio_queue = audio_queue
        self._utt_event_queue = event_queue
        self._utt_worker = worker
        self._utt_last_text = ""
        self._utt_opened = opened
        self._utt_last_text_box = last_text_box
        worker.start()
        # Wait until the websocket is open so early push_audio is not dropped.
        await asyncio.to_thread(opened.wait, 10)
        if not opened.is_set():
            await self.cancel_utterance()
            raise SpeechError("DashScope ASR websocket open timed out")

    async def push_audio(self, chunk: bytes) -> None:
        """Send one PCM (or wav) chunk into the active utterance."""
        if self._utt_audio_queue is None:
            raise SpeechError("begin_utterance() must be called before push_audio()")
        if not chunk:
            return
        payload = _strip_wav_header(chunk) if self._option.format == "pcm" else chunk
        if payload:
            self._utt_audio_queue.put(payload)

    async def end_utterance(self) -> AsyncIterator[SpeechRecognizeEvent]:
        """Finish the utterance and yield recognition events."""
        if self._utt_audio_queue is None or self._utt_event_queue is None:
            raise SpeechError("begin_utterance() must be called before end_utterance()")

        self._utt_audio_queue.put(None)
        saw_final = False
        try:
            while True:
                item = await self._utt_event_queue.get()
                if item is None:
                    break
                if isinstance(item, BaseException):
                    yield SpeechRecognizeEvent(type="error", message=str(item))
                    return
                if item.type == "final":
                    saw_final = True
                yield item

            last_text = getattr(self, "_utt_last_text_box", {}).get("text", "")
            if not saw_final:
                if last_text:
                    yield SpeechRecognizeEvent(type="final", text=last_text)
                else:
                    logger.warning(f"{self}: empty transcription from DashScope")
                    yield SpeechRecognizeEvent(type="final", text="")
        finally:
            if self._utt_worker is not None:
                self._utt_worker.join(timeout=30)
            self._utt_audio_queue = None
            self._utt_event_queue = None
            self._utt_worker = None

    async def cancel_utterance(self) -> None:
        """Abort an in-flight utterance without yielding events."""
        if self._utt_audio_queue is not None:
            self._utt_audio_queue.put(None)
        if self._utt_event_queue is not None:
            self._utt_event_queue.put_nowait(None)
        if self._utt_worker is not None:
            self._utt_worker.join(timeout=30)
        self._utt_audio_queue = None
        self._utt_event_queue = None
        self._utt_worker = None

    async def stream_async(
        self,
        audio: bytes | AsyncIterator[bytes],
    ) -> AsyncIterator[SpeechRecognizeEvent]:
        await self.begin_utterance()
        try:
            if isinstance(audio, (bytes, bytearray)):
                for frame in _iter_pcm_frames(bytes(audio)):
                    await self.push_audio(frame)
            else:
                async for chunk in audio:
                    await self.push_audio(chunk)
            async for event in self.end_utterance():
                yield event
        except Exception:
            await self.cancel_utterance()
            raise


class DashScopeSpeechSynthesizer(SpeechSynthesizer):
    """DashScope ``audio.tts_v2`` synthesizer with streaming PCM output."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_TTS_MODEL,
        option: SpeechSynthesisOption | None = None,
        voice: str | None = None,
    ) -> None:
        self._id = str(uuid4())
        self._api_key = _resolve_api_key(api_key)
        self._model = model
        if option is None:
            option = SpeechSynthesisOption(
                voice=voice or DEFAULT_TTS_VOICE,
                format="pcm",
                sample_rate=24000,
            )
        elif voice is not None:
            option = option.model_copy(update={"voice": voice})
        self._option = option
        self._entered = False

    @property
    def id(self) -> str:
        return self._id

    def get_option(self) -> SpeechSynthesisOption:
        return self._option

    async def __aenter__(self) -> Self:
        dashscope.api_key = self._api_key
        self._entered = True
        return self

    async def __aexit__(self, *exc: object) -> None:
        self._entered = False

    async def stream_async(
        self,
        text: str | AsyncIterator[str],
    ) -> AsyncIterator[bytes]:
        if not self._entered:
            raise SpeechError(
                f"{type(self).__name__} must be entered before stream_async"
            )

        if isinstance(text, str):
            content = text
        else:
            parts: list[str] = []
            async for part in text:
                parts.append(part)
            content = "".join(parts)
        if not content:
            return

        loop = asyncio.get_running_loop()
        audio_queue: asyncio.Queue[bytes | None | BaseException] = asyncio.Queue()

        class _Callback(ResultCallback):
            def on_data(self, data: bytes) -> None:
                if data:
                    loop.call_soon_threadsafe(audio_queue.put_nowait, bytes(data))

            def on_complete(self) -> None:
                loop.call_soon_threadsafe(audio_queue.put_nowait, None)

            def on_error(self, message) -> None:
                loop.call_soon_threadsafe(
                    audio_queue.put_nowait,
                    SpeechError(f"DashScope TTS error: {message}"),
                )
                loop.call_soon_threadsafe(audio_queue.put_nowait, None)

        def _worker() -> None:
            try:
                synthesizer = DashScopeTTSV2Client(
                    model=self._model,
                    voice=self._option.voice,
                    format=self._dashscope_audio_format(self._option.sample_rate),
                    callback=_Callback(),
                )
                synthesizer.streaming_call(content)
                synthesizer.streaming_complete()
            except BaseException as exc:  # noqa: BLE001 - bridge to async consumer
                loop.call_soon_threadsafe(audio_queue.put_nowait, exc)
                loop.call_soon_threadsafe(audio_queue.put_nowait, None)

        worker = threading.Thread(target=_worker, name="dashscope-tts", daemon=True)
        worker.start()
        try:
            while True:
                item = await audio_queue.get()
                if item is None:
                    break
                if isinstance(item, BaseException):
                    raise SpeechError(f"DashScope TTS error: {item}") from item
                yield item
        finally:
            worker.join(timeout=30)

    @staticmethod
    def _dashscope_audio_format(sample_rate: int) -> TTSV2AudioFormat:
        mapping = {
            8000: TTSV2AudioFormat.PCM_8000HZ_MONO_16BIT,
            16000: TTSV2AudioFormat.PCM_16000HZ_MONO_16BIT,
            22050: TTSV2AudioFormat.PCM_22050HZ_MONO_16BIT,
            24000: TTSV2AudioFormat.PCM_24000HZ_MONO_16BIT,
            44100: TTSV2AudioFormat.PCM_44100HZ_MONO_16BIT,
            48000: TTSV2AudioFormat.PCM_48000HZ_MONO_16BIT,
        }
        try:
            return mapping[sample_rate]
        except KeyError as e:
            raise ValueError(
                f"DashScope TTS PCM does not support sample_rate={sample_rate}"
            ) from e
