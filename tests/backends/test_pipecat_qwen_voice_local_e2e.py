"""Opt-in local mic/speaker e2e for Pipecat + Qwen Audio.

Requires:
  - DASHSCOPE_API_KEY
  - PIPECAT_LOCAL_AUDIO_E2E=1
  - PortAudio / PyAudio and a working microphone + speaker

Speak one short phrase into the mic after the test starts; wait for the
assistant to reply. The session ends via idle timeout after a completed turn.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest

from fivcplayground.agents import AgentRunStatus
from fivcplayground.agents.types.repositories import FileAgentRunRepository
from fivcplayground.backends.pipecat.metrics import VoiceLatencyTracker
from fivcplayground.utils import OutputDir

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_HAS_KEY = bool(os.environ.get("DASHSCOPE_API_KEY", "").strip())
_OPT_IN = os.environ.get("PIPECAT_LOCAL_AUDIO_E2E", "").strip() == "1"


def _has_local_audio() -> bool:
    try:
        import pyaudio
    except ImportError:
        return False
    audio = pyaudio.PyAudio()
    try:
        return audio.get_device_count() > 0
    finally:
        audio.terminate()


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not _HAS_KEY or not _OPT_IN,
        reason=(
            "Set DASHSCOPE_API_KEY and PIPECAT_LOCAL_AUDIO_E2E=1 "
            "to run the local Qwen voice e2e"
        ),
    ),
    pytest.mark.skipif(
        not _has_local_audio(),
        reason="PyAudio / local audio devices are not available",
    ),
]


@pytest.mark.asyncio
async def test_local_qwen_voice_completes_one_turn(tmp_path):
    from examples.pipecat_qwen_voice._common import (
        BUILTIN_TOOL_IDS,
        build_tool_retriever,
        build_voice_stack,
        stt_trailing_silence_secs,
        warmup_voice_stack,
    )

    # Short idle so the session ends soon after the assistant finishes speaking.
    stack = build_voice_stack(idle_timeout_secs=45)
    tool_retriever = await build_tool_retriever()
    await warmup_voice_stack(
        stack["stt"],
        stack["tts"],
        llm=getattr(stack["agent"], "_agent_model", None),
    )
    session_id = f"qwen-voice-e2e-{uuid4()}"
    repo = FileAgentRunRepository(output_dir=OutputDir(str(tmp_path)).subdir("runs"))

    print(
        "\nSpeak one short phrase into the microphone now; "
        "wait for the spoken reply (idle timeout 45s).\n",
        flush=True,
    )

    latency = VoiceLatencyTracker()
    try:
        await stack["agent"].run_async(
            transport=stack["transport"],
            stt=stack["stt"],
            tts=stack["tts"],
            vad=stack["vad"],
            tool_retriever=tool_retriever,
            tool_ids=list(BUILTIN_TOOL_IDS),
            stt_trailing_silence_secs=stt_trailing_silence_secs(),
            agent_run_repository=repo,
            agent_run_session_id=session_id,
            latency_tracker=latency,
        )
    finally:
        latency.print_report()

    runs = await repo.list_agent_runs_async(session_id)
    completed = [
        run
        for run in runs
        if run.status == AgentRunStatus.COMPLETED
        and run.query
        and run.query.text
        and run.reply
        and run.reply.text
    ]
    assert completed, (
        "Expected at least one completed user+assistant turn in AgentRun. "
        "Speak clearly into the mic after the test starts."
    )
    last = completed[-1]
    assert last.query.text.strip()
    assert last.reply.text.strip()
