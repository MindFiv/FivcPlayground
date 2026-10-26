"""Unit tests for VoiceLatencyTracker and LatencyProbe."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from fivcplayground.backends.pipecat.metrics import LatencyProbe, VoiceLatencyTracker
from pipecat.frames.frames import (
    LLMContextFrame,
    LLMTextFrame,
    TextFrame,
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameDirection


def test_voice_latency_tracker_as_dict_ms():
    tracker = VoiceLatencyTracker()
    tracker.stt_first_audio_at = 1.0
    tracker.stt_first_result_at = 1.25
    tracker.llm_first_input_at = 1.3
    tracker.llm_first_output_at = 1.8
    tracker.tts_first_input_at = 1.85
    tracker.tts_first_output_at = 2.1

    data = tracker.as_dict()
    assert data["stt_ms"] == 250.0
    assert data["llm_ms"] == 500.0
    assert data["tts_ms"] == 250.0
    assert data["e2e_ms"] == 1100.0


def test_voice_latency_tracker_marks_only_first():
    tracker = VoiceLatencyTracker()
    tracker.mark_stt_first_audio()
    first = tracker.stt_first_audio_at
    time.sleep(0.01)
    tracker.mark_stt_first_audio()
    assert tracker.stt_first_audio_at == first

    tracker.mark_stt_first_result()
    first_result = tracker.stt_first_result_at
    tracker.mark_stt_first_result()
    assert tracker.stt_first_result_at == first_result

    tracker.mark_llm_first_input()
    tracker.mark_llm_first_output()
    tracker.mark_tts_first_input()
    tracker.mark_tts_first_output()
    llm_in = tracker.llm_first_input_at
    llm_out = tracker.llm_first_output_at
    tts_in = tracker.tts_first_input_at
    tts_out = tracker.tts_first_output_at
    tracker.mark_llm_first_input()
    tracker.mark_llm_first_output()
    tracker.mark_tts_first_input()
    tracker.mark_tts_first_output()
    assert tracker.llm_first_input_at == llm_in
    assert tracker.llm_first_output_at == llm_out
    assert tracker.tts_first_input_at == tts_in
    assert tracker.tts_first_output_at == tts_out


def test_voice_latency_tracker_missing_phases_are_none():
    tracker = VoiceLatencyTracker()
    data = tracker.as_dict()
    assert data["e2e_ms"] is None
    assert data["stt_ms"] is None
    assert data["llm_ms"] is None
    assert data["tts_ms"] is None


def test_format_report_contains_metric_keys():
    tracker = VoiceLatencyTracker()
    tracker.stt_first_audio_at = 1.0
    tracker.tts_first_output_at = 2.0
    report = tracker.format_report()
    assert "e2e_ms:" in report
    assert "stt_ms:" in report
    assert "llm_ms:" in report
    assert "tts_ms:" in report
    assert "1000.0" in report


@pytest.mark.asyncio
async def test_latency_probe_llm_in_marks_only_context_frame():
    tracker = VoiceLatencyTracker()
    probe = LatencyProbe(tracker, role="llm_in")
    probe.push_frame = AsyncMock()

    # Non-context frames must not mark.
    await probe.process_frame(
        TranscriptionFrame("hi", "", "now"), FrameDirection.DOWNSTREAM
    )
    assert tracker.llm_first_input_at is None

    context = MagicMock()
    await probe.process_frame(LLMContextFrame(context), FrameDirection.DOWNSTREAM)
    assert tracker.llm_first_input_at is not None
    first = tracker.llm_first_input_at

    await probe.process_frame(LLMContextFrame(context), FrameDirection.DOWNSTREAM)
    assert tracker.llm_first_input_at == first
    assert probe.push_frame.await_count == 3


@pytest.mark.asyncio
async def test_latency_probe_llm_out_marks_only_llm_text_frame():
    tracker = VoiceLatencyTracker()
    probe = LatencyProbe(tracker, role="llm_out")
    probe.push_frame = AsyncMock()

    await probe.process_frame(TextFrame(text="plain"), FrameDirection.DOWNSTREAM)
    assert tracker.llm_first_output_at is None

    await probe.process_frame(LLMTextFrame(text="hello"), FrameDirection.DOWNSTREAM)
    assert tracker.llm_first_output_at is not None
    first = tracker.llm_first_output_at

    await probe.process_frame(LLMTextFrame(text="again"), FrameDirection.DOWNSTREAM)
    assert tracker.llm_first_output_at == first
    assert probe.push_frame.await_count == 3
