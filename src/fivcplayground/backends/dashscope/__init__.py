"""Optional DashScope backend (speech recognition and synthesis).

Import submodules after selecting this backend so the DashScope SDK remains
an optional dependency for other backends.
"""

__all__ = [
    "DEFAULT_STT_MODEL",
    "DEFAULT_TTS_MODEL",
    "DEFAULT_TTS_VOICE",
    "DashScopeSpeechRecognizer",
    "DashScopeSpeechSynthesizer",
    "configure_dashscope_websocket_url",
]

from .speeches import (
    DEFAULT_STT_MODEL,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
    DashScopeSpeechRecognizer,
    DashScopeSpeechSynthesizer,
    configure_dashscope_websocket_url,
)
