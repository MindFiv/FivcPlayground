"""Tests for extra, backend-specific configuration fields."""

import tempfile

import pytest
import yaml
from fivcplayground.agents.types.base import AgentConfig
from fivcplayground.agents.types.repositories.files import FileAgentConfigRepository
from fivcplayground.models.types.base import ModelConfig
from fivcplayground.models.types.repositories.files import FileModelConfigRepository
from fivcplayground.utils import OutputDir


class TestModelConfigExtra:
    def test_extra_defaults_to_none_for_legacy_configs(self):
        config = ModelConfig(id="test", provider="openai", model="gpt-4o-mini")

        assert config.extra is None

    def test_extra_round_trips_json_data(self):
        data = {
            "id": "test",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "extra": {
                "organization": "org-1",
                "default_headers": {"X-Environment": "dev"},
            },
        }

        config = ModelConfig.model_validate(data)

        assert ModelConfig.model_validate(config.model_dump(mode="json")) == config

    @pytest.mark.parametrize(
        "key",
        [
            "id",
            "description",
            "provider",
            "model",
            "api_key",
            "base_url",
            "temperature",
            "max_tokens",
            "enable_thinking",
        ],
    )
    def test_extra_cannot_override_canonical_model_fields(self, key):
        with pytest.raises(ValueError, match="canonical ModelConfig field"):
            ModelConfig(
                id="test",
                provider="openai",
                model="gpt-4o-mini",
                extra={key: "override"},
            )


class TestAgentConfigExtra:
    def test_extra_defaults_to_none_for_legacy_configs(self):
        config = AgentConfig(id="test-agent")

        assert config.extra is None

    def test_extra_round_trips_json_data(self):
        data = {
            "id": "test-agent",
            "extra": {
                "pipeline_params": {"enable_metrics": True},
                "idle_timeout_secs": 120,
            },
        }

        config = AgentConfig.model_validate(data)

        assert AgentConfig.model_validate(config.model_dump(mode="json")) == config


class TestConfigExtraRepositories:
    @pytest.mark.asyncio
    async def test_model_repository_round_trips_extra(self):
        config = ModelConfig(
            id="pipecat-chat",
            provider="openai",
            model="gpt-4o-mini",
            extra={"organization": "org-1"},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = FileModelConfigRepository(output_dir=OutputDir(tmpdir))
            await repository.update_model_config_async(config)

            loaded = await repository.get_model_config_async("pipecat-chat")

            assert loaded == config

    @pytest.mark.asyncio
    async def test_agent_repository_round_trips_extra(self):
        config = AgentConfig(
            id="voice-agent",
            extra={"pipeline_params": {"enable_metrics": True}},
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = FileAgentConfigRepository(output_dir=OutputDir(tmpdir))
            await repository.update_agent_config_async(config)

            loaded = await repository.get_agent_config_async("voice-agent")

            assert loaded == config

    @pytest.mark.asyncio
    async def test_yaml_directly_exposes_extra(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repository = FileAgentConfigRepository(output_dir=OutputDir(tmpdir))
            await repository.update_agent_config_async(
                AgentConfig(id="voice-agent", extra={"idle_timeout_secs": 120})
            )
            with open(repository._get_agents_file(), encoding="utf-8") as stream:
                data = yaml.safe_load(stream)

            assert data["voice-agent"]["extra"] == {"idle_timeout_secs": 120}
