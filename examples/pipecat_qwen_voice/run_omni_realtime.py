#!/usr/bin/env python
"""Run a Qwen-Omni realtime voice agent on the local microphone and speaker.

Prerequisites:
  - Python 3.11+
  - ``brew install portaudio`` (macOS)
  - ``uv sync --extra pipecat-local --extra dashscope --extra dev``
  - ``DASHSCOPE_API_KEY``
  - ``DASHSCOPE_REALTIME_BASE_URL`` (full ``wss://.../api-ws/v1/realtime``)

Speak into the mic; the assistant replies through the speakers. Idle timeout
(default 120s) or Ctrl+C ends the session. Headphones avoid speaker echo
tripping server-side VAD.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

# Allow ``python examples/pipecat_qwen_voice/run_omni_realtime.py`` without install.
_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from examples.pipecat_qwen_voice._common import (  # noqa: E402
    BUILTIN_TOOL_IDS,
    DEFAULT_IDLE_TIMEOUT_SECS,
    build_realtime_stack,
    build_tool_retriever,
)

load_dotenv()


async def main() -> None:
    stack = build_realtime_stack(idle_timeout_secs=DEFAULT_IDLE_TIMEOUT_SECS)
    tool_retriever = await build_tool_retriever()
    print(
        "Qwen-Omni realtime session started. Speak into the microphone.\n"
        f"Builtin tools: {', '.join(BUILTIN_TOOL_IDS)}.\n"
        f"Idle timeout: {DEFAULT_IDLE_TIMEOUT_SECS}s. Press Ctrl+C to stop.\n"
        "Use headphones so speaker audio does not trigger server VAD.\n",
        flush=True,
    )
    try:
        result = await stack["agent"].run_async(
            transport=stack["transport"],
            tool_retriever=tool_retriever,
            tool_ids=list(BUILTIN_TOOL_IDS),
        )
        text = getattr(result, "text", None) or ""
        if text:
            print(f"Last assistant reply: {text}")
    except KeyboardInterrupt:
        print("\nInterrupted; shutting down.")


if __name__ == "__main__":
    asyncio.run(main())
