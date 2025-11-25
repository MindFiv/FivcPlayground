from langchain_core.language_models import BaseChatModel as Model

from fivcplayground.models.types.base import ModelConfig


def create_model(model_config: ModelConfig) -> Model:
    if model_config.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_config.model,
            api_key=model_config.api_key,
            base_url=model_config.base_url,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
        )
    elif model_config.provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model_config.model,
            base_url=model_config.base_url,
            temperature=model_config.temperature,
            reasoning=False,
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_config.provider}")
