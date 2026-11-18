"""Unused implement-specific kwargs must be accepted and ignored."""

import tempfile

import pytest
from fivcplayground.agents.types import AgentConfig, AgentRunSession
from fivcplayground.agents.types.repositories.files import (
    FileAgentConfigRepository,
    FileAgentRunRepository,
)
from fivcplayground.agents.types.repositories.sqlite import SqliteAgentRunRepository
from fivcplayground.embeddings.types.base import EmbeddingConfig
from fivcplayground.embeddings.types.repositories.files import (
    FileEmbeddingConfigRepository,
)
from fivcplayground.models.types.base import ModelConfig
from fivcplayground.models.types.repositories.files import FileModelConfigRepository
from fivcplayground.skills.types.base import SkillConfig
from fivcplayground.skills.types.repositories.files import FileSkillConfigRepository
from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.tools.types.repositories.files import FileToolConfigRepository
from fivcplayground.utils import OutputDir


@pytest.mark.asyncio
async def test_file_agent_config_repository_ignores_unused_kwargs():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileAgentConfigRepository(output_dir=OutputDir(tmpdir))
        config = AgentConfig(
            id="kwargs-agent",
            description="desc",
            system_prompt="prompt",
        )
        await repo.update_agent_config_async(config, unused_flag=True)
        loaded = await repo.get_agent_config_async("kwargs-agent", unused_flag=True)
        assert loaded is not None
        assert loaded.id == "kwargs-agent"
        listed = await repo.list_agent_configs_async(unused_flag=True)
        assert len(listed) == 1
        await repo.delete_agent_config_async("kwargs-agent", unused_flag=True)
        assert await repo.get_agent_config_async("kwargs-agent") is None


@pytest.mark.asyncio
async def test_file_agent_run_repository_ignores_unused_kwargs():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileAgentRunRepository(output_dir=OutputDir(tmpdir))
        session = AgentRunSession(
            agent_id="kwargs-run-agent",
            description="session",
        )
        await repo.update_agent_run_session_async(session, unused_flag=True)
        loaded = await repo.get_agent_run_session_async(session.id, unused_flag=True)
        assert loaded is not None
        sessions = await repo.list_agent_run_sessions_async(unused_flag=True)
        assert len(sessions) == 1
        runs = await repo.list_agent_runs_async(session.id, unused_flag=True)
        assert runs == []
        await repo.delete_agent_run_session_async(session.id, unused_flag=True)
        assert await repo.get_agent_run_session_async(session.id) is None


@pytest.mark.asyncio
async def test_sqlite_agent_run_repository_ignores_unused_kwargs():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = SqliteAgentRunRepository(output_dir=OutputDir(tmpdir))
        try:
            session = AgentRunSession(
                agent_id="kwargs-sqlite-agent",
                description="session",
            )
            await repo.update_agent_run_session_async(session, unused_flag=True)
            loaded = await repo.get_agent_run_session_async(
                session.id, unused_flag=True
            )
            assert loaded is not None
            sessions = await repo.list_agent_run_sessions_async(unused_flag=True)
            assert len(sessions) == 1
            runs = await repo.list_agent_runs_async(session.id, unused_flag=True)
            assert runs == []
            await repo.delete_agent_run_session_async(session.id, unused_flag=True)
            assert await repo.get_agent_run_session_async(session.id) is None
        finally:
            repo.close()


@pytest.mark.asyncio
async def test_file_model_config_repository_ignores_unused_kwargs():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileModelConfigRepository(output_dir=OutputDir(tmpdir))
        config = ModelConfig(
            id="kwargs-model",
            model="gpt-4",
            provider="openai",
        )
        await repo.update_model_config_async(config, unused_flag=True)
        loaded = await repo.get_model_config_async("kwargs-model", unused_flag=True)
        assert loaded is not None
        listed = await repo.list_model_configs_async(unused_flag=True)
        assert len(listed) == 1
        await repo.delete_model_config_async("kwargs-model", unused_flag=True)
        assert await repo.get_model_config_async("kwargs-model") is None


@pytest.mark.asyncio
async def test_file_tool_config_repository_ignores_unused_kwargs():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileToolConfigRepository(output_dir=OutputDir(tmpdir))
        config = ToolConfig(
            id="kwargs-tool",
            description="tool",
            transport="stdio",
            command="echo",
        )
        await repo.update_tool_config_async(config, unused_flag=True)
        loaded = await repo.get_tool_config_async("kwargs-tool", unused_flag=True)
        assert loaded is not None
        listed = await repo.list_tool_configs_async(unused_flag=True)
        assert len(listed) == 1
        await repo.delete_tool_config_async("kwargs-tool", unused_flag=True)
        assert await repo.get_tool_config_async("kwargs-tool") is None


@pytest.mark.asyncio
async def test_file_embedding_config_repository_ignores_unused_kwargs():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileEmbeddingConfigRepository(output_dir=OutputDir(tmpdir))
        config = EmbeddingConfig(
            id="kwargs-emb",
            provider="openai",
            model="text-embedding-ada-002",
        )
        await repo.update_embedding_config_async(config, unused_flag=True)
        loaded = await repo.get_embedding_config_async("kwargs-emb", unused_flag=True)
        assert loaded is not None
        listed = await repo.list_embedding_configs_async(unused_flag=True)
        assert len(listed) == 1
        await repo.delete_embedding_config_async("kwargs-emb", unused_flag=True)
        assert await repo.get_embedding_config_async("kwargs-emb") is None


@pytest.mark.asyncio
async def test_file_skill_config_repository_ignores_unused_kwargs():
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileSkillConfigRepository(output_dir=OutputDir(tmpdir))
        config = SkillConfig(
            id="kwargs-skill",
            description="skill",
            instructions="do things",
        )
        await repo.update_skill_config_async(config, unused_flag=True)
        loaded = await repo.get_skill_config_async("kwargs-skill", unused_flag=True)
        assert loaded is not None
        listed = await repo.list_skill_configs_async(unused_flag=True)
        assert len(listed) == 1
        await repo.delete_skill_config_async("kwargs-skill", unused_flag=True)
        assert await repo.get_skill_config_async("kwargs-skill") is None