# Backend Selection Guide

FivcPlayground has explicit model, tool, and agent backend implementations. **Strands** is the default CLI backend; **Google ADK** is an alternative text backend; **Pipecat** is an optional backend for transport-backed real-time pipelines (and CLI text via stdio).

## Backend Matrix

| Backend | Extra | Best for |
|---------|-------|----------|
| Strands | `strands` | Default text agents and native tool orchestration |
| Google ADK | `adk` | Alternative text agents in Google's ADK runtime |
| Pipecat | `pipecat` | Transport-backed voice/realtime pipelines; CLI text via stdio (no PyAudio) |
| Pipecat local audio | `pipecat-local` | Local mic/speaker (`LocalAudioTransport` / PyAudio); includes `pipecat` |
| DashScope | `dashscope` | Qwen Audio STT/TTS (`SpeechRecognizer` / `SpeechSynthesizer`) |

## Select A Backend

```bash
uv sync --extra pipecat
fivcplayground run Generic --backend pipecat --query "What is machine learning?"
```

CLI `--query` seeds a `StdioTransport` with a `StringIO` (one line, then EOF). Programmatically, omit `transport` to use real stdin/stdout, or pass a live transport (local mic/speakers, WebSocket, etc.):

```python
from fivcplayground.backends.pipecat.agents import PipecatAgentBackend
from fivcplayground.backends.pipecat.models import PipecatModelBackend
from fivcplayground.backends.pipecat.tools import PipecatToolBackend
from fivcplayground.backends.pipecat.transports import StdioTransport
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

model_backend = PipecatModelBackend()
tool_backend = PipecatToolBackend()
agent_backend = PipecatAgentBackend()

# Text session (stdin/stdout); stt/tts are ignored when transport is None/StdioTransport defaulting
await agent.run_async()  # transport=None → StdioTransport()

# Or seed one query like the CLI:
from io import StringIO
await agent.run_async(transport=StdioTransport(input_stream=StringIO("Hello\n")))

# Local mic/speaker full-duplex voice (see examples/pipecat_qwen_voice/):
transport = LocalAudioTransport(
    LocalAudioTransportParams(audio_in_enabled=True, audio_out_enabled=True)
)
# Pass SpeechRecognizer / SpeechSynthesizer from backends.dashscope
# (e.g. DashScopeSpeechRecognizer / DashScopeSpeechSynthesizer),
# plus vad for segmented STT. Pipecat STT/TTS adapters wrap them internally.
await agent.run_async(
    transport=transport,
    stt=stt,
    tts=tts,
    vad=SileroVADAnalyzer(),
)
```

### Qwen local voice example

End-to-end local microphone/speaker demo with Alibaba Cloud Qwen Audio:

- Example: [`examples/pipecat_qwen_voice/`](../examples/pipecat_qwen_voice/) (`run_local.py` + README)
- STT/TTS: `backends.dashscope` (`DashScopeSpeechRecognizer` / `DashScopeSpeechSynthesizer`); Pipecat only adapts them into the pipeline
- Models: `qwen-audio-3.1-asr-flash-streaming` / `qwen-audio-3.1-tts-flash` (voice `longanhuan_v3.1`)
- Requires `DASHSCOPE_API_KEY`, PortAudio (`brew install portaudio` on macOS), and `uv sync --extra pipecat-local --extra dashscope`

```bash
uv run python examples/pipecat_qwen_voice/run_local.py

# Opt-in live e2e (speak one turn into the mic):
DASHSCOPE_API_KEY=... PIPECAT_LOCAL_AUDIO_E2E=1 \
  uv run pytest -m e2e tests/backends/test_pipecat_qwen_voice_local_e2e.py -v
```

Default pytest runs exclude `e2e` (`-m "not e2e"`).

## Pipecat Runtime Settings

Serializable backend settings live under `extra`. Canonical fields remain first-class; `extra` is interpreted by the selected backend and is not logged by default.

```yaml
# models.yaml
pipecat-chat:
  provider: openai
  model: gpt-4o-mini
  api_key: ${OPENAI_API_KEY}
  extra:
    organization: org_...
    default_headers:
      X-Environment: dev
---
# agents.yaml
voice-agent:
  model_id: pipecat-chat
  extra:
    pipeline_params:
      enable_metrics: true
      enable_usage_metrics: true
    idle_timeout_secs: 120
```

When `transport` is `None`, a text `StdioTransport` is used and `stt` / `tts` are ignored. For non-stdio transports, optional `SpeechRecognizer` / `SpeechSynthesizer` instances are wrapped as Pipecat `STTService` / `TTSService` and injected into the pipeline. Transports and speech objects are non-serializable runtime objects and never belong in `extra`.

Turn transcripts are persisted via aggregator event handlers (`on_user_turn_stopped`, `on_assistant_turn_stopped`) into `AgentRun` records when a session repository is supplied. Tool calls are not recorded on `AgentRun`.
