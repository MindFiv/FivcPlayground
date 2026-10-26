"""Speech recognition and synthesis interfaces.

Implementation-agnostic STT/TTS so agents and backends can use audio without
depending on a vendor SDK. Concrete adapters implement ``SpeechRecognizer``
and ``SpeechSynthesizer``.

The same recognizer or synthesizer instance is reusable across turns: enter
the async context once, then call ``stream_async`` once per turn.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Literal, Self

from pydantic import BaseModel, Field


class SpeechError(Exception):
    """Base error for speech recognition and synthesis."""


class SpeechRecognizeOption(BaseModel):
    """Optional hints captured when the recognizer is created."""

    language: str | None = None
    enable_itn: bool = False
    hot_words: list[str] | None = None
    context: str | None = None
    format: str = "pcm"
    sample_rate: int = 16000
    channels: int = 1
    extra: dict[str, Any] = Field(default_factory=dict)


class SpeechRecognizeEvent(BaseModel):
    """One recognition event. ``text`` is set for partial/final; ``message`` for error."""

    type: Literal["partial", "final", "error"]
    text: str = ""
    language: str | None = None
    message: str | None = None


class SpeechRecognizer(ABC):
    """Reusable speech recognizer. Enter once, then ``stream_async`` per turn."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Stable identifier for this recognizer instance."""

    @abstractmethod
    def get_option(self) -> SpeechRecognizeOption:
        """Return the recognition options captured at creation."""

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Acquire resources for recognition."""

    @abstractmethod
    async def __aexit__(self, *exc: object) -> None:
        """Release recognition resources."""

    @abstractmethod
    async def stream_async(
        self,
        audio: bytes | AsyncIterator[bytes],
    ) -> AsyncIterator[SpeechRecognizeEvent]:
        """Yield ``partial`` / ``final`` / ``error`` events for one utterance.

        ``bytes`` is a complete clip. An async byte iterator is one utterance;
        exhaustion is the commit.
        """


class SpeechSynthesisOption(BaseModel):
    """Optional synthesis parameters captured when the synthesizer is created."""

    voice: str
    format: str = "mp3"
    sample_rate: int = 22050
    volume: int = Field(default=50, ge=0, le=100)
    speech_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch_rate: float = Field(default=1.0, ge=0.5, le=2.0)
    extra: dict[str, Any] = Field(default_factory=dict)


class SpeechSynthesizer(ABC):
    """Reusable speech synthesizer. Enter once, then ``stream_async`` per turn."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Stable identifier for this synthesizer instance."""

    @abstractmethod
    def get_option(self) -> SpeechSynthesisOption:
        """Return the synthesis options captured at creation."""

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Acquire resources for synthesis."""

    @abstractmethod
    async def __aexit__(self, *exc: object) -> None:
        """Release synthesis resources."""

    @abstractmethod
    async def stream_async(
        self,
        text: str | AsyncIterator[str],
    ) -> AsyncIterator[bytes]:
        """Yield encoded audio for one text or streamed-text turn."""
