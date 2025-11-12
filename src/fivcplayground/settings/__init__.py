__all__ = [
    "config",
    "default_embedder_config",
    "default_llm_config",
    "chat_llm_config",
    "reasoning_llm_config",
    "coding_llm_config",
    "agent_logger_config",
    "default_logger_config",
    "SettingsConfig",
]

import os
from fivcplayground.utils import (
    create_lazy_value,
    create_default_kwargs,
)
from fivcplayground.settings.types import SettingsConfig


def _load_config():
    config_file = os.environ.get("SETTINGS_FILE", "settings.yaml")
    config_file = os.path.abspath(config_file)
    return SettingsConfig(config_file)


config = create_lazy_value(_load_config)

default_framework = create_lazy_value(
    lambda: config.get("default_framework") or "strands"
)

default_embedder_config = create_lazy_value(
    lambda: create_default_kwargs(
        config.get("default_embedder") or {},
        {
            "provider": "openai",
            "model": "text-embedding-v3",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "dimension": 1024,
        },
    )
)

default_llm_config = create_lazy_value(
    lambda: create_default_kwargs(
        config.get("default_llm") or {},
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "temperature": 0.5,
        },
    )
)

chat_llm_config = create_lazy_value(
    lambda: create_default_kwargs(
        config.get("chat_llm") or {},
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "temperature": 1.0,
        },
    )
)

reasoning_llm_config = create_lazy_value(
    lambda: create_default_kwargs(
        config.get("reasoning_llm") or {},
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "temperature": 0.1,
        },
    )
)

coding_llm_config = create_lazy_value(
    lambda: create_default_kwargs(
        config.get("coding_llm") or {},
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "temperature": 0.1,
        },
    )
)

agent_logger_config = create_lazy_value(
    lambda: create_default_kwargs(
        config.get("agent_logger") or {},
        {
            "level": "INFO",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
    )
)

default_logger_config = create_lazy_value(
    lambda: create_default_kwargs(
        config.get("default_logger") or {},
        {
            "level": "INFO",
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
    )
)
