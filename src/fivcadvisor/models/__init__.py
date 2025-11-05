__all__ = [
    "create_default_model",
    "create_chat_model",
    "create_reasoning_model",
    "create_coding_model",
]

from fivcadvisor import settings, utils
from fivcadvisor.models.backends import (
    create_model,
    Model,
)


def create_default_model(**kwargs) -> Model:
    """
    Factory function to create a LangChain LLM instance.

    This function maintains backward compatibility with the Strands model API
    while using LangChain models under the hood.

    Args:
        **kwargs: Model configuration (provider, model, api_key, temperature, etc.)

    Returns:
        LangChain LLM instance

    Raises:
        ValueError: If provider is not specified or unsupported
    """

    kwargs = utils.create_default_kwargs(kwargs, settings.default_llm_config)

    # Call create_model on the backend module
    return create_model(**kwargs)


def create_chat_model(**kwargs) -> Model:
    """
    Factory function to create a LangChain LLM instance for chat.

    Uses the chat_llm_config from settings for default configuration.

    Args:
        **kwargs: Model configuration (overrides defaults)

    Returns:
        LangChain LLM instance configured for chat
    """

    return create_default_model(
        **utils.create_default_kwargs(kwargs, settings.chat_llm_config)
    )


def create_reasoning_model(**kwargs) -> Model:
    """
    Factory function to create a LangChain LLM instance for reasoning tasks.

    Uses the reasoning_llm_config from settings for default configuration.

    Args:
        **kwargs: Model configuration (overrides defaults)

    Returns:
        LangChain LLM instance configured for reasoning
    """
    # Set defaults from env if available

    return create_default_model(
        **utils.create_default_kwargs(kwargs, settings.reasoning_llm_config)
    )


def create_coding_model(**kwargs) -> Model:
    """
    Factory function to create a LangChain LLM instance for coding tasks.

    Uses the coding_llm_config from settings for default configuration.

    Args:
        **kwargs: Model configuration (overrides defaults)

    Returns:
        LangChain LLM instance configured for coding
    """
    # Set defaults from env if available

    return create_default_model(
        **utils.create_default_kwargs(kwargs, settings.coding_llm_config)
    )
