__all__ = [
    "DEFAULT_EMBEDDING_ARGS",
    "DEFAULT_LLM_ARGS",
    "CHAT_LLM_ARGS",
    "REASONING_LLM_ARGS",
    "CODING_LLM_ARGS",
    "Config",
    "ConfigSession",
]

import os
from typing import Dict, cast

from fivcglue.interfaces import (
    IComponentSite,
    configs,
)
from fivcglue.implements.utils import (
    ComponentSite,
)
from fivcplayground.utils import (
    DefaultKwargs,
    LazyValue,
)
from fivcplayground.settings.types import Config, ConfigSession


def _load_component_site() -> IComponentSite:
    """Load and initialize the default component site.

    This creates a ComponentSite and registers the default settings config.
    """

    site = ComponentSite()

    # Load default settings config from file
    config_file = os.environ.get("SETTINGS_FILE", "settings.yaml")
    config_file = os.path.abspath(config_file)
    config_impl = Config(site, config_file=config_file)

    site.register_component(configs.IConfig, config_impl)
    return site


def _load_config_session(conf_session: configs.IConfigSession) -> Dict[str, str]:
    """Load a configuration session into a dictionary."""
    return {k: conf_session.get_value(k) for k in conf_session.list_keys()}


def _load_config(component_site: IComponentSite, session_name: str) -> Dict[str, str]:
    """Load a configuration into a dictionary."""
    conf = cast(configs.IConfig, component_site.get_component(configs.IConfig))
    conf_session = conf.get_session(session_name)
    return _load_config_session(conf_session) if conf_session else {}


default_component_site = LazyValue(_load_component_site)

_DEFAULT_EMBEDDING_ARGS = DefaultKwargs(
    {
        "provider": "openai",
        "model": "text-embedding-v3",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "dimension": 1024,
    }
)

_DEFAULT_LLM_ARGS = DefaultKwargs(
    {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "temperature": 0.5,
    }
)

DEFAULT_EMBEDDING_ARGS = LazyValue(
    lambda: _DEFAULT_EMBEDDING_ARGS(
        _load_config(cast(IComponentSite, default_component_site), "default_embedding")
    )
)

DEFAULT_LLM_ARGS = LazyValue(
    lambda: _DEFAULT_LLM_ARGS(
        _load_config(cast(IComponentSite, default_component_site), "default_llm")
    )
)

CHAT_LLM_ARGS = LazyValue(
    lambda: _DEFAULT_LLM_ARGS(
        _load_config(cast(IComponentSite, default_component_site), "chat_llm")
    )
)

REASONING_LLM_ARGS = LazyValue(
    lambda: _DEFAULT_LLM_ARGS(
        _load_config(cast(IComponentSite, default_component_site), "reasoning_llm")
    )
)

CODING_LLM_ARGS = LazyValue(
    lambda: _DEFAULT_LLM_ARGS(
        _load_config(cast(IComponentSite, default_component_site), "coding_llm")
    )
)
