"""
Model implementations for FivcPlayground.

This module provides implementations of IModel and IModelProvider interfaces,
enabling flexible model creation and management through the component architecture.

Classes:
    ModelImpl: Implementation of IModel interface for LLM models
    ModelProviderImpl: Implementation of IModelProvider interface for model creation
"""

from typing import Any, Iterable

from fivcglue import IComponentSite
from fivcglue.interfaces.utils import query_component

from fivcplayground.interfaces import IModel, IModelProvider, ISettingProvider


def _openai_model(
    model: str = "gpt-4o-mini",
    api_key: str = "",
    base_url: str = "https://api.openai.com/v1",
    temperature: float = 0.5,
    max_tokens: int = 4096,
    **kwargs,
) -> Any:
    """
    Create an OpenAI model instance.

    Args:
        model: Model name (e.g., "gpt-4", "gpt-4o-mini")
        api_key: OpenAI API key
        base_url: Base URL for OpenAI API (default: https://api.openai.com/v1)
        temperature: Temperature for sampling (0-2)
        max_tokens: Maximum tokens in response
        **kwargs: Additional arguments (ignored)

    Returns:
        OpenAIModel instance
    """
    from strands.models.openai import OpenAIModel

    return OpenAIModel(
        client_args={
            "api_key": api_key,
            "base_url": base_url,
        },
        model_id=model,
        params={
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
    )


def _ollama_model(
    model: str = "llama2",
    base_url: str = "http://localhost:11434",
    temperature: float = 0.5,
    **kwargs,
) -> Any:
    """
    Create an Ollama model instance.

    Args:
        model: Model name (e.g., "llama2", "mistral")
        base_url: Ollama server URL (default: http://localhost:11434)
        temperature: Temperature for sampling (0-2)
        **kwargs: Additional arguments (ignored)

    Returns:
        OllamaModel instance
    """
    from strands.models.ollama import OllamaModel

    return OllamaModel(
        base_url,
        model_id=model,
        temperature=temperature,
    )


def _create_model(provider: str = "openai", **kwargs: Any) -> Any:
    """
    Create a model instance based on provider type.

    Routes model creation to the appropriate provider-specific function.

    Args:
        provider: The model provider ("openai" or "ollama")
        **kwargs: Provider-specific configuration parameters

    Returns:
        A model instance (OpenAIModel or OllamaModel)

    Raises:
        ValueError: If the provider is not supported
    """
    if provider == "openai":
        return _openai_model(**kwargs)
    elif provider == "ollama":
        return _ollama_model(**kwargs)
    else:
        raise ValueError(f"Unsupported model provider: {provider}")


class ModelImpl(IModel):
    """
    Implementation of IModel interface with lazy loading support.

    This class represents a single LLM model instance with metadata and
    lazy-loaded access to the underlying model object. The actual model
    instantiation is deferred until get_underlying() is first called.

    Example:
        >>> model = ModelImpl("default_llm", provider="openai", model="gpt-4o-mini")
        >>> model.name
        'default_llm'
        >>> underlying = model.get_underlying()  # Model created on first call
        >>> underlying2 = model.get_underlying()  # Cached model returned
    """

    def __init__(self, name: str, **config: Any):
        """
        Initialize a model instance with lazy loading.

        Args:
            name: Name of the model (e.g., "default_llm", "chat_llm")
            **config: Model configuration parameters (provider, model, api_key, etc.)
                     These are stored for lazy instantiation on first access.
        """
        self._name = name
        self._config = config
        self._underlying = None  # Lazy-loaded on first access

    @property
    def name(self) -> str:
        """Get the name of the model."""
        return self._name

    def get_underlying(self) -> Any:
        """
        Get the underlying model object with lazy loading.

        On first call, creates the Strands Model based on stored configuration
        and caches it for subsequent calls.

        Returns:
            The underlying model instance (e.g., OpenAIModel, OllamaModel)
        """
        if self._underlying is None:
            self._underlying = _create_model(**self._config)
        return self._underlying


class ModelProviderImpl(IModelProvider):
    """
    Implementation of IModelProvider interface.

    This class provides access to LLM models configured through the settings provider.
    It loads model configurations from settings and creates model instances on demand.

    The provider expects settings to be organized with model names as keys and
    configuration dictionaries as values. Each configuration should include:
    - provider: The model provider (e.g., "openai", "ollama")
    - model: The model name (e.g., "gpt-4o-mini", "llama2")
    - Additional provider-specific parameters (api_key, temperature, etc.)

    Example:
        >>> from fivcplayground.settings import default_component_site
        >>> from fivcplayground.interfaces import IModelProvider
        >>> provider = default_component_site.get_component(IModelProvider)
        >>> model = provider.get_model("default_llm")
        >>> if model:
        ...     print(f"Model: {model.name}")

    Configuration file example (settings.yaml):
        default_llm:
          provider: openai
          model: gpt-4o-mini
          api_key: sk-...
          temperature: 0.5
        chat_llm:
          provider: openai
          model: gpt-4o-mini
          temperature: 1.0
    """

    def __init__(self, component_site: IComponentSite, **kwargs: Any):
        """
        Initialize the model provider.

        Args:
            component_site: An IComponentSite instance for component registration
            **kwargs: Additional keyword arguments (unused, for compatibility)
        """
        self._models_cache = {}  # Cache for created models
        self._component_site = component_site
        self._setting_provider = query_component(
            component_site, ISettingProvider, "models"
        )

        if self._setting_provider is None:
            raise ValueError("No setting provider found")

    def get_model(
        self,
        name: str,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> IModel | None:
        """
        Get a model instance by name with lazy loading.

        Retrieves the model configuration from settings and returns a ModelImpl
        instance with lazy loading. The actual model instantiation is deferred
        until get_underlying() is called. ModelImpl instances are cached to avoid
        redundant configuration lookups.

        Args:
            name: Name of the model to retrieve (e.g., "default_llm", "chat_llm")
            user_id: Optional user ID for multi-user support (isolates user data)
            **kwargs: Additional configuration parameters (overrides settings)

        Returns:
            A ModelImpl instance if the model exists, None otherwise.
            Returns None if the model name is not found in settings.

        Raises:
            AttributeError: If setting doesn't have list() method
            TypeError: If iteration over setting.list() fails
            ValueError: If invalid configuration values are encountered
        """
        # Check cache first
        if name in self._models_cache:
            return self._models_cache[name]

        # Get model configuration from settings
        setting = self._setting_provider.get_setting(name, user_id)
        if setting is None:
            return None

        # Build configuration from setting
        config = {}
        for key, value in setting.list():
            config[key] = value

        # Override with any provided kwargs
        config.update(kwargs)

        # Create ModelImpl with lazy loading (model creation deferred)
        model = ModelImpl(name, **config)

        # Cache the ModelImpl instance
        self._models_cache[name] = model

        return model

    def list_models(
        self,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> Iterable[IModel]:
        """
        List all available models.

        Iterates through all settings and attempts to create model instances
        for each one. Models that fail to create are skipped.

        Args:
            user_id: Optional user ID for multi-user support (isolates user data)
            **kwargs: Additional configuration parameters

        Returns:
            An iterable of ModelImpl instances for all successfully created models.
        """
        for setting in self._setting_provider.list_settings(user_id, **kwargs):
            model = self.get_model(setting.name, user_id, **kwargs)
            if model is not None:
                yield model
