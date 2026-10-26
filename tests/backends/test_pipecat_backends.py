"""Focused tests for Pipecat configuration and runtime assembly."""

from unittest.mock import patch

import pytest
from fivcplayground.models.types.base import ModelConfig


class TestPipecatModelBackend:
    def test_canonical_and_extra_constructor_arguments(self):
        from fivcplayground.backends.pipecat.models import PipecatModelBackend

        model_config = ModelConfig(
            id="pipecat-chat",
            provider="openai",
            model="gpt-4o-mini",
            api_key="key",
            base_url="https://example.test/v1",
            temperature=0.2,
            max_tokens=256,
            enable_thinking=False,
            extra={
                "organization": "org-1",
                "default_headers": {"X-Environment": "dev"},
            },
        )

        from pipecat.services.openai.llm import OpenAILLMService

        with patch(
            "fivcplayground.backends.pipecat.models.OpenAILLMService"
        ) as service:
            service.Settings = OpenAILLMService.Settings
            backend = PipecatModelBackend()
            model = backend.create_model(model_config)

        kwargs = service.call_args.kwargs
        settings = kwargs["settings"]
        assert model.get_underlying() is service.return_value
        assert isinstance(settings, OpenAILLMService.Settings)
        assert settings.model == "gpt-4o-mini"
        assert settings.temperature == 0.2
        assert settings.max_completion_tokens == 256
        assert settings.extra == {"extra_body": {"enable_thinking": False}}
        assert kwargs["api_key"] == "key"
        assert kwargs["base_url"] == "https://example.test/v1"
        assert kwargs["organization"] == "org-1"
        assert kwargs["default_headers"] == {"X-Environment": "dev"}
        # Constructor kwargs are ignored by Pipecat 1.13; set on the instance.
        assert "supports_developer_role" not in kwargs
        assert service.return_value.supports_developer_role is False

    def test_openai_default_base_url_keeps_developer_role(self):
        from fivcplayground.backends.pipecat.models import PipecatModelBackend

        model_config = ModelConfig(
            id="openai-default",
            provider="openai",
            model="gpt-4o-mini",
            api_key="key",
        )

        from pipecat.services.openai.llm import OpenAILLMService

        with patch(
            "fivcplayground.backends.pipecat.models.OpenAILLMService"
        ) as service:
            service.Settings = OpenAILLMService.Settings
            # Mimic class default so we can detect whether create_model mutates it.
            service.return_value.supports_developer_role = True
            PipecatModelBackend().create_model(model_config)

        kwargs = service.call_args.kwargs
        assert "supports_developer_role" not in kwargs
        assert service.return_value.supports_developer_role is True

    def test_ollama_canonical_and_extra_constructor_arguments(self):
        from fivcplayground.backends.pipecat.models import PipecatModelBackend

        model_config = ModelConfig(
            id="local",
            provider="ollama",
            model="qwen3",
            base_url="http://127.0.0.1:11434/v1",
            temperature=0.1,
            extra={"organization": "local-org"},
        )

        from pipecat.services.ollama.llm import OLLamaLLMService

        with patch(
            "fivcplayground.backends.pipecat.models.OLLamaLLMService"
        ) as service:
            service.Settings = OLLamaLLMService.Settings
            backend = PipecatModelBackend()
            backend.create_model(model_config)

        kwargs = service.call_args.kwargs
        settings = kwargs["settings"]
        assert isinstance(settings, OLLamaLLMService.Settings)
        assert settings.model == "qwen3"
        assert settings.temperature == 0.1
        assert settings.max_completion_tokens is None
        assert kwargs["base_url"] == "http://127.0.0.1:11434/v1"
        assert kwargs["organization"] == "local-org"


class TestPipecatToolBackend:
    @pytest.mark.asyncio
    async def test_callable_becomes_executing_function_schema(self):
        from fivcplayground.backends.pipecat.tools import PipecatToolBackend

        async def echo(a: str, b: int = 2) -> str:
            """Echo values."""
            return f"{a}:{b}"

        tool = PipecatToolBackend().create_tool(echo)
        schema = tool.get_underlying()
        assert schema.name == "echo"
        assert schema.description == "Echo values."
        assert schema.properties["a"]["type"] == "string"
        assert schema.required == ["a"]

        class Params:
            arguments = {"a": "hi"}
            results: list[str]

            async def result_callback(self, value):
                self.results.append(value)

        params = Params()
        params.results = []
        await schema.handler(params)
        assert params.results == ["hi:2"]
