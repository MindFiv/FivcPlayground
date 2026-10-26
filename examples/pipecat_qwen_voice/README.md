# Pipecat + Qwen local mic/speaker voice

Full-duplex voice session using FivcPlayground’s Pipecat backend with:

- **STT:** `qwen-audio-3.1-asr-flash-streaming` (live PCM streaming while you speak; websocket opens on VAD start, not after you finish)
- **TTS:** `qwen-audio-3.1-tts-flash` / voice `longanhuan_v3.1` (streaming PCM via `DashScopeSpeechSynthesizer`)
- **LLM:** DashScope OpenAI-compatible (`qwen-turbo` by default; override with `PIPECAT_QWEN_LLM_MODEL`)
- **Tools:** all built-ins (`auxiliary` = clock + calculator, `filesystem`, `shell`) via `PipecatToolBackend` — no Chroma required
- **Transport:** `LocalAudioTransport` (system microphone + speakers)

## Setup

```bash
# macOS system dependency for PyAudio
brew install portaudio

uv sync --extra pipecat --extra dashscope --extra dev
export DASHSCOPE_API_KEY=sk-...
# Optional (workspace WebSocket endpoint; reduces cross-region RTT):
# export DASHSCOPE_BASE_WEBSOCKET_API_URL=wss://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/api-ws/v1/inference
```

Optional device selection (PyAudio device indexes):

```bash
export PIPECAT_AUDIO_IN_DEVICE=1
export PIPECAT_AUDIO_OUT_DEVICE=2
```

Latency-related env (optional):

```bash
# Silero VAD stop hang (default 0.2s; Pipecat's built-in TTFS assumes 0.2)
export PIPECAT_VAD_STOP_SECS=0.2
# Silence appended after VAD stop before STT finalize (default 0.1s)
export PIPECAT_STT_TRAILING_SILENCE=0.1
# Faster/slower LLM
export PIPECAT_QWEN_LLM_MODEL=qwen-turbo
```

`run_local.py` warms up STT/TTS once before accepting mic input so the first turn is closer to steady-state latency.

## Run

```bash
uv run python examples/pipecat_qwen_voice/run_local.py
```

Speak a short phrase; wait for the spoken reply. The session ends after
`idle_timeout_secs` (default 120) of inactivity, or with Ctrl+C.

Tip: for speaker echo / self-barge-in issues, prefer headphones while
testing, or lower speaker volume.

## Opt-in e2e test

Default `make test` / pytest excludes `e2e`. To run the live local-audio test
(you must speak one turn into the mic):

```bash
DASHSCOPE_API_KEY=... PIPECAT_LOCAL_AUDIO_E2E=1 \
  uv run pytest -m e2e tests/backends/test_pipecat_qwen_voice_local_e2e.py -v
```
