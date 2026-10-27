#!/usr/bin/env python
"""Run a full-duplex Qwen voice agent on the local microphone and speaker.

Prerequisites:
  - Python 3.11+
  - ``brew install portaudio`` (macOS)
  - ``uv sync --extra pipecat-local --extra dashscope --extra dev``
  - ``DASHSCOPE_API_KEY`` set (and optionally ``DASHSCOPE_BASE_WEBSOCKET_API_URL``)

Speak into the mic; the assistant replies through the speakers. Idle timeout
(default 120s) or Ctrl+C ends the session.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow ``python examples/pipecat_qwen_voice/run_local.py`` without install.
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from examples.pipecat_qwen_voice._common import (  # noqa: E402
    BUILTIN_TOOL_IDS,
    DEFAULT_IDLE_TIMEOUT_SECS,
    build_tool_retriever,
    build_voice_stack,
    stt_trailing_silence_secs,
    warmup_voice_stack,
)
from fivcplayground.backends.pipecat.metrics import VoiceLatencyTracker  # noqa: E402

load_dotenv()


async def main() -> None:
    stack = build_voice_stack(idle_timeout_secs=DEFAULT_IDLE_TIMEOUT_SECS)
    tool_retriever = await build_tool_retriever()
    agent = stack["agent"]
    print("Warming up STT/TTS/LLM…", flush=True)
    await warmup_voice_stack(
        stack["stt"], stack["tts"], llm=getattr(agent, "_agent_model", None)
    )
    print(
        "Qwen local voice session started. Speak into the microphone.\n"
        f"Builtin tools: {', '.join(BUILTIN_TOOL_IDS)}.\n"
        f"Idle timeout: {DEFAULT_IDLE_TIMEOUT_SECS}s. Press Ctrl+C to stop.\n",
        flush=True,
    )
    latency = VoiceLatencyTracker()
    try:
        result = await agent.run_async(
            transport=stack["transport"],
            stt=stack["stt"],
            tts=stack["tts"],
            vad=stack["vad"],
            tool_retriever=tool_retriever,
            tool_ids=list(BUILTIN_TOOL_IDS),
            stt_trailing_silence_secs=stt_trailing_silence_secs(),
            latency_tracker=latency,
        )
        text = getattr(result, "text", None) or ""
        if text:
            print(f"Last assistant reply: {text}")
    except KeyboardInterrupt:
        print("\nInterrupted; shutting down.")
    finally:
        latency.print_report()


if __name__ == "__main__":
    asyncio.run(main())
