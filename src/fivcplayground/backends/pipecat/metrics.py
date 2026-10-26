"""First-packet latency tracking for Pipecat voice pipelines."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

from pipecat.frames.frames import Frame, LLMContextFrame, LLMTextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


def _ms(start: float | None, end: float | None) -> float | None:
    if start is None or end is None:
        return None
    return round((end - start) * 1000.0, 3)


@dataclass
class VoiceLatencyTracker:
    """Record first-audio / first-result timings for one voice turn.

    Only the first mark for each phase is kept so multi-turn idle sessions
    do not overwrite the e2e measurement.
    """

    stt_first_audio_at: float | None = None
    stt_first_result_at: float | None = None
    llm_first_input_at: float | None = None
    llm_first_output_at: float | None = None
    tts_first_input_at: float | None = None
    tts_first_output_at: float | None = None
    wall_epoch_at: float = field(default_factory=time.time)
    perf_origin_at: float = field(default_factory=time.perf_counter)

    def _now(self) -> float:
        return time.perf_counter()

    def mark_stt_first_audio(self) -> None:
        if self.stt_first_audio_at is None:
            self.stt_first_audio_at = self._now()

    def mark_stt_first_result(self) -> None:
        if self.stt_first_result_at is None:
            self.stt_first_result_at = self._now()

    def mark_llm_first_input(self) -> None:
        if self.llm_first_input_at is None:
            self.llm_first_input_at = self._now()

    def mark_llm_first_output(self) -> None:
        if self.llm_first_output_at is None:
            self.llm_first_output_at = self._now()

    def mark_tts_first_input(self) -> None:
        if self.tts_first_input_at is None:
            self.tts_first_input_at = self._now()

    def mark_tts_first_output(self) -> None:
        if self.tts_first_output_at is None:
            self.tts_first_output_at = self._now()

    def as_dict(self) -> dict[str, Any]:
        return {
            "e2e_ms": _ms(self.stt_first_audio_at, self.tts_first_output_at),
            "stt_ms": _ms(self.stt_first_audio_at, self.stt_first_result_at),
            "llm_ms": _ms(self.llm_first_input_at, self.llm_first_output_at),
            "tts_ms": _ms(self.tts_first_input_at, self.tts_first_output_at),
            "stt_first_audio_at": self.stt_first_audio_at,
            "stt_first_result_at": self.stt_first_result_at,
            "llm_first_input_at": self.llm_first_input_at,
            "llm_first_output_at": self.llm_first_output_at,
            "tts_first_input_at": self.tts_first_input_at,
            "tts_first_output_at": self.tts_first_output_at,
            "wall_epoch_at": self.wall_epoch_at,
            "perf_origin_at": self.perf_origin_at,
        }

    def format_report(self) -> str:
        data = self.as_dict()
        lines = [
            "=== Voice latency metrics ===",
            f"e2e_ms:  {data['e2e_ms']}",
            f"stt_ms:  {data['stt_ms']}",
            f"llm_ms:  {data['llm_ms']}",
            f"tts_ms:  {data['tts_ms']}",
            "--- raw timestamps (perf_counter) ---",
            f"stt_first_audio_at:  {data['stt_first_audio_at']}",
            f"stt_first_result_at: {data['stt_first_result_at']}",
            f"llm_first_input_at:  {data['llm_first_input_at']}",
            f"llm_first_output_at: {data['llm_first_output_at']}",
            f"tts_first_input_at:  {data['tts_first_input_at']}",
            f"tts_first_output_at: {data['tts_first_output_at']}",
            f"wall_epoch_at:       {data['wall_epoch_at']}",
            f"perf_origin_at:      {data['perf_origin_at']}",
        ]
        return "\n".join(lines)

    def print_report(self) -> None:
        print(self.format_report(), flush=True)


LatencyProbeRole = Literal["llm_in", "llm_out"]


class LatencyProbe(FrameProcessor):
    """Pass-through probe that marks LLM first-input / first-output timings."""

    def __init__(
        self,
        tracker: VoiceLatencyTracker,
        role: LatencyProbeRole,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._tracker = tracker
        self._role = role

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if direction == FrameDirection.DOWNSTREAM:
            if self._role == "llm_in" and isinstance(frame, LLMContextFrame):
                self._tracker.mark_llm_first_input()
            elif self._role == "llm_out" and isinstance(frame, LLMTextFrame):
                self._tracker.mark_llm_first_output()
        await self.push_frame(frame, direction)
