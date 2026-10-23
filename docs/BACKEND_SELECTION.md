# Backend Selection Guide

FivcPlayground has explicit model, tool, and agent backend implementations. **Strands** is the default CLI backend; **Google ADK** is an alternative text backend; **Pipecat** is an optional backend for transport-backed real-time pipelines (and CLI text via stdio).

## Backend Matrix

| Backend | Extra | Python | Best for |
|---------|-------|--------|----------|
| Strands | `strands` | 3.10+ | Default text agents and native tool orchestration |
| Google ADK | `adk` | 3.10+ | Alternative text agents in Google's ADK runtime |
| Pipecat | `pipecat` | 3.11+ | Transport-backed voice/realtime pipelines; CLI text via stdio |

## Select A Backend

```bash
uv sync --extra pipecat
fivcplayground run Generic --backend pipecat --query "What is machine learning?"
```

CLI `--query` seeds a `StdioTransport` with a `StringIO` (one line, then EOF). Programmatically, omit `transport` to use real stdin/stdout, or pass a live transport (WebSocket, etc.):

```python
from fivcplayground.backends.pipecat.agents import PipecatAgentBackend
from fivcplayground.backends.pipecat.models import PipecatModelBackend
from fivcplayground.backends.pipecat.tools import PipecatToolBackend
from fivcplayground.backends.pipecat.transports import StdioTransport
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

model_backend = PipecatModelBackend()
tool_backend = PipecatToolBackend()
agent_backend = PipecatAgentBackend()

# Text session (stdin/stdout); stt/tts are ignored when transport is None/StdioTransport defaulting
await agent.run_async()  # transport=None → StdioTransport()

# Or seed one query like the CLI:
from io import StringIO
await agent.run_async(transport=StdioTransport(input_stream=StringIO("Hello\n")))

# Voice / websocket session:
transport = FastAPIWebsocketTransport(
    websocket=websocket,
    params=FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        add_wav_header=False,
        serializer=ProtobufFrameSerializer(),
    ),
)
await agent.run_async(transport=transport, stt=stt, tts=tts)
```

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

When `transport` is `None`, a text `StdioTransport` is used and `stt` / `tts` are ignored. For non-stdio transports, optional `stt` / `tts` processors are injected into the pipeline. Transports, STT, and TTS are non-serializable runtime objects and never belong in `extra`.

Turn transcripts are persisted via aggregator event handlers (`on_user_turn_stopped`, `on_assistant_turn_stopped`) into `AgentRun` records when a session repository is supplied. Tool calls are not recorded on `AgentRun`.
