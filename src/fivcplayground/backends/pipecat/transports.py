"""Text stdin/stdout transport for Pipecat pipelines."""

from __future__ import annotations

import asyncio
import sys
from typing import TextIO

from pipecat.frames.frames import (
    CancelFrame,
    EndFrame,
    Frame,
    LLMFullResponseEndFrame,
    LLMTextFrame,
    StartFrame,
    TranscriptionFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.base_transport import BaseTransport
from pipecat.utils.time import time_now_iso8601


class _StdioInputProcessor(FrameProcessor):
    """Read lines from a text stream and emit user-turn frames."""

    def __init__(self, transport: "StdioTransport", input_stream: TextIO, **kwargs):
        super().__init__(**kwargs)
        self._transport = transport
        self._input_stream = input_stream
        self._read_task: asyncio.Task | None = None

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            await self.push_frame(frame, direction)
            if self._read_task is None:
                self._read_task = self.create_task(self._read_loop())
            return

        if isinstance(frame, (EndFrame, CancelFrame)):
            await self._stop_reader()
            await self.push_frame(frame, direction)
            return

        await self.push_frame(frame, direction)

    async def cleanup(self):
        await self._stop_reader()
        await super().cleanup()

    async def _stop_reader(self):
        if self._read_task is not None:
            await self.cancel_task(self._read_task)
            self._read_task = None

    async def _read_loop(self):
        loop = asyncio.get_running_loop()
        try:
            while True:
                line = await loop.run_in_executor(None, self._input_stream.readline)
                if line == "":
                    await self._transport.notify_eof()
                    return
                text = line.rstrip("\r\n")
                if not text:
                    continue
                self._transport.mark_user_turn_sent()
                # Transcription drives turn start; UserStoppedSpeaking closes it.
                await self.push_frame(
                    TranscriptionFrame(
                        text=text,
                        user_id="stdio",
                        timestamp=time_now_iso8601(),
                        finalized=True,
                    )
                )
                await self.push_frame(UserStoppedSpeakingFrame())
        except asyncio.CancelledError:
            raise


class _StdioOutputProcessor(FrameProcessor):
    """Write assistant text frames to a text stream."""

    def __init__(self, transport: "StdioTransport", output_stream: TextIO, **kwargs):
        super().__init__(**kwargs)
        self._transport = transport
        self._output_stream = output_stream

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, LLMTextFrame):
            self._output_stream.write(frame.text)
            self._output_stream.flush()
        elif isinstance(frame, LLMFullResponseEndFrame):
            self._output_stream.write("\n")
            self._output_stream.flush()
            await self._transport.notify_response_done()

        await self.push_frame(frame, direction)


class StdioTransport(BaseTransport):
    """Line-oriented stdin/stdout transport for text-only Pipecat sessions."""

    def __init__(
        self,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
        *,
        name: str | None = None,
    ):
        super().__init__(name=name or "StdioTransport")
        self._input_stream = sys.stdin if input_stream is None else input_stream
        self._output_stream = sys.stdout if output_stream is None else output_stream
        self._input: _StdioInputProcessor | None = None
        self._output: _StdioOutputProcessor | None = None
        self._eof = False
        self._pending_response = False
        # sync=True so disconnect handlers (e.g. runner.cancel) finish before return
        self._register_event_handler("on_client_disconnected", sync=True)

    def input(self) -> FrameProcessor:
        if self._input is None:
            self._input = _StdioInputProcessor(
                self, self._input_stream, name=self._input_name
            )
        return self._input

    def output(self) -> FrameProcessor:
        if self._output is None:
            self._output = _StdioOutputProcessor(
                self, self._output_stream, name=self._output_name
            )
        return self._output

    def mark_user_turn_sent(self):
        self._pending_response = True

    async def notify_eof(self):
        self._eof = True
        if not self._pending_response:
            await self._emit_disconnected()

    async def notify_response_done(self):
        self._pending_response = False
        if self._eof:
            await self._emit_disconnected()

    async def _emit_disconnected(self):
        await self._call_event_handler("on_client_disconnected", None)
