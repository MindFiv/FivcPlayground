# Repository Interface `**kwargs` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add trailing `**kwargs` to every config/run repository ABC method and matching File/Sqlite implementation so callers can pass implement-specific options; unused kwargs are silently ignored; no behavior change for existing callers.

**Architecture:** Mechanical signature alignment. Agent ABCs already have `**kwargs` (uncommitted local edit in `agents/.../base.py`). Extend the same pattern to models/tools/embeddings/skills ABCs and all concrete repos. Document the hybrid convention in `ARCHITECTURE_PATTERNS.md`. Tests prove unused kwargs do not raise and do not alter results.

**Tech Stack:** Python 3, ABC/`abstractmethod`, pytest + pytest-asyncio, existing File/Sqlite repositories.

**Spec:** `docs/superpowers/specs/2026-11-18-repository-kwargs-design.md`

---

## File Map

| File | Responsibility |
|------|----------------|
| `src/fivcplayground/agents/types/repositories/base.py` | Agent ABCs (already updated; include in commit) |
| `src/fivcplayground/agents/types/repositories/files.py` | File agent config + run implementations |
| `src/fivcplayground/agents/types/repositories/sqlite.py` | Sqlite agent run implementation |
| `src/fivcplayground/models/types/repositories/base.py` | ModelConfigRepository ABC |
| `src/fivcplayground/models/types/repositories/files.py` | File model implementation |
| `src/fivcplayground/tools/types/repositories/base.py` | ToolConfigRepository ABC |
| `src/fivcplayground/tools/types/repositories/files.py` | File tool implementation |
| `src/fivcplayground/embeddings/types/repositories/base.py` | EmbeddingConfigRepository ABC |
| `src/fivcplayground/embeddings/types/repositories/files.py` | File embedding implementation |
| `src/fivcplayground/skills/types/repositories/base.py` | SkillConfigRepository ABC |
| `src/fivcplayground/skills/types/repositories/files.py` | File skill implementation |
| `docs/ARCHITECTURE_PATTERNS.md` | Document kwargs convention |
| `tests/test_repository_kwargs.py` | New focused kwargs acceptance tests |

---

### Task 1: Failing tests for unused kwargs

**Files:**
- Create: `tests/test_repository_kwargs.py`

- [ ] **Step 1: Write the failing test file**

Create `tests/test_repository_kwargs.py` with:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_repository_kwargs.py -v
```

Expected: FAIL with `TypeError: ... got an unexpected keyword argument 'unused_flag'` on methods that lack `**kwargs` (agent File/Sqlite and non-list methods on other repos). Model/tool/embedding `list_*` already accept kwargs and will pass that sub-call alone; overall tests still fail.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_repository_kwargs.py
git commit -m "$(cat <<'EOF'
test: add failing coverage for repository unused kwargs

Prove File/Sqlite repository methods must accept implement-specific kwargs without changing results.
EOF
)"
```

---

### Task 2: Agent repository implementations accept `**kwargs`

**Files:**
- Modify: `src/fivcplayground/agents/types/repositories/files.py` (all `*_async` public methods on `FileAgentConfigRepository` and `FileAgentRunRepository`)
- Modify: `src/fivcplayground/agents/types/repositories/sqlite.py` (all `*_async` public methods on `SqliteAgentRunRepository`)
- Keep: `src/fivcplayground/agents/types/repositories/base.py` (already has `**kwargs`; include in commit)

- [ ] **Step 1: Update `FileAgentConfigRepository` signatures**

Change each method to accept trailing `**kwargs` without reading it. Example shape:

```python
async def update_agent_config_async(
    self,
    agent_config: AgentConfig,
    **kwargs,
) -> None:
    # existing body unchanged

async def get_agent_config_async(
    self,
    agent_id: str,
    **kwargs,
) -> Optional[AgentConfig]:
    # existing body unchanged

async def list_agent_configs_async(self, **kwargs) -> List[AgentConfig]:
    # existing body unchanged

async def delete_agent_config_async(
    self,
    agent_id: str,
    **kwargs,
) -> None:
    # existing body unchanged
```

- [ ] **Step 2: Update `FileAgentRunRepository` signatures**

Same pattern for:

- `update_agent_run_session_async(self, agent: AgentRunSession, **kwargs)`
- `get_agent_run_session_async(self, session_id: str, **kwargs)`
- `list_agent_run_sessions_async(self, **kwargs)`
- `delete_agent_run_session_async(self, session_id: str, **kwargs)`
- `update_agent_run_async(self, session_id: str, agent_run: AgentRun, **kwargs)`
- `get_agent_run_async(self, session_id: str, run_id: str, **kwargs)`
- `delete_agent_run_async(self, session_id: str, run_id: str, **kwargs)`
- `list_agent_runs_async(self, session_id: str, **kwargs)`

Bodies unchanged.

- [ ] **Step 3: Update `SqliteAgentRunRepository` signatures**

Mirror the same eight method signatures as Step 2 (parameter names may stay `agent` for session where the current file uses that name). Bodies unchanged.

- [ ] **Step 4: Run agent-focused kwargs tests**

Run:

```bash
uv run pytest tests/test_repository_kwargs.py::test_file_agent_config_repository_ignores_unused_kwargs tests/test_repository_kwargs.py::test_file_agent_run_repository_ignores_unused_kwargs tests/test_repository_kwargs.py::test_sqlite_agent_run_repository_ignores_unused_kwargs -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add \
  src/fivcplayground/agents/types/repositories/base.py \
  src/fivcplayground/agents/types/repositories/files.py \
  src/fivcplayground/agents/types/repositories/sqlite.py
git commit -m "$(cat <<'EOF'
feat: accept **kwargs on agent repository methods

Allow implement-specific options through AgentConfig/AgentRun repository ABCs; File and Sqlite ignore unused kwargs.
EOF
)"
```

---

### Task 3: Other config repository ABCs accept `**kwargs` on all methods

**Files:**
- Modify: `src/fivcplayground/models/types/repositories/base.py`
- Modify: `src/fivcplayground/tools/types/repositories/base.py`
- Modify: `src/fivcplayground/embeddings/types/repositories/base.py`
- Modify: `src/fivcplayground/skills/types/repositories/base.py`

- [ ] **Step 1: Update `ModelConfigRepository`**

Replace method signatures with:

```python
@abstractmethod
async def update_model_config_async(
    self,
    model_config: ModelConfig,
    **kwargs,
) -> None:
    """Create or update a model configuration."""

@abstractmethod
async def get_model_config_async(
    self,
    model_id: str,
    **kwargs,
) -> ModelConfig | None:
    """Retrieve a model configuration by ID."""

@abstractmethod
async def list_model_configs_async(self, **kwargs) -> List[ModelConfig]:
    """List all model configurations in the repository."""

@abstractmethod
async def delete_model_config_async(
    self,
    model_id: str,
    **kwargs,
) -> None:
    """Delete a model configuration."""
```

(`list_*` already has `**kwargs`; keep it.)

- [ ] **Step 2: Update `ToolConfigRepository`**

Same four-method pattern with `tool_config` / `tool_id` / `ToolConfig`.

- [ ] **Step 3: Update `EmbeddingConfigRepository`**

Same four-method pattern with `embedding_config` / `embedding_id` / `EmbeddingConfig`. Keep multiline formatting consistent with the file.

- [ ] **Step 4: Update `SkillConfigRepository`**

```python
@abstractmethod
async def get_skill_config_async(
    self,
    skill_id: str,
    **kwargs,
) -> SkillConfig | None:
    """Retrieve a skill configuration by ID."""

@abstractmethod
async def list_skill_configs_async(self, **kwargs) -> List[SkillConfig]:
    """List all skill configurations."""

@abstractmethod
async def update_skill_config_async(
    self,
    skill_config: SkillConfig,
    **kwargs,
) -> None:
    """Create or update a skill configuration."""

@abstractmethod
async def delete_skill_config_async(
    self,
    skill_id: str,
    **kwargs,
) -> None:
    """Delete a skill configuration."""
```

- [ ] **Step 5: Commit ABCs**

```bash
git add \
  src/fivcplayground/models/types/repositories/base.py \
  src/fivcplayground/tools/types/repositories/base.py \
  src/fivcplayground/embeddings/types/repositories/base.py \
  src/fivcplayground/skills/types/repositories/base.py
git commit -m "$(cat <<'EOF'
feat: add **kwargs to remaining config repository ABCs

Align model/tool/embedding/skill repository interfaces with the agent kwargs convention.
EOF
)"
```

---

### Task 4: Other File repository implementations accept `**kwargs`

**Files:**
- Modify: `src/fivcplayground/models/types/repositories/files.py`
- Modify: `src/fivcplayground/tools/types/repositories/files.py`
- Modify: `src/fivcplayground/embeddings/types/repositories/files.py`
- Modify: `src/fivcplayground/skills/types/repositories/files.py`

- [ ] **Step 1: Update File model/tool/embedding/skill method signatures**

For each of the four File repos, add `**kwargs` to `update_*`, `get_*`, `list_*` (if missing), and `delete_*`. Do not change method bodies.

Model example:

```python
async def update_model_config_async(
    self,
    model_config: ModelConfig,
    **kwargs,
) -> None:
    # existing body

async def get_model_config_async(
    self,
    model_id: str,
    **kwargs,
) -> ModelConfig | None:
    # existing body

async def list_model_configs_async(self, **kwargs) -> List[ModelConfig]:
    # existing body (already had **kwargs)

async def delete_model_config_async(
    self,
    model_id: str,
    **kwargs,
) -> None:
    # existing body
```

Apply the analogous changes for tools, embeddings, and skills.

- [ ] **Step 2: Run remaining kwargs tests**

Run:

```bash
uv run pytest tests/test_repository_kwargs.py -v
```

Expected: all tests PASS

- [ ] **Step 3: Commit**

```bash
git add \
  src/fivcplayground/models/types/repositories/files.py \
  src/fivcplayground/tools/types/repositories/files.py \
  src/fivcplayground/embeddings/types/repositories/files.py \
  src/fivcplayground/skills/types/repositories/files.py
git commit -m "$(cat <<'EOF'
feat: accept **kwargs on model/tool/embedding/skill file repos

Mirror ABC signatures so unused implement-specific kwargs are silently ignored.
EOF
)"
```

---

### Task 5: Document the repository kwargs convention

**Files:**
- Modify: `docs/ARCHITECTURE_PATTERNS.md`

- [ ] **Step 1: Update the Repository Pattern section**

In `docs/ARCHITECTURE_PATTERNS.md`, replace the abstract/concrete example under “### 1. Repository Pattern” so signatures include `**kwargs`, and add a short convention note after the Benefits/Used for block (before “### 2. Factory Pattern”):

```markdown
**Structure**:
```python
# Abstract interface with async methods
class AgentConfigRepository(ABC):
    @abstractmethod
    async def get_agent_config_async(
        self,
        agent_id: str,
        **kwargs,
    ) -> AgentConfig | None:
        """Retrieve an agent configuration by ID."""
        pass


# Concrete implementation
class FileAgentConfigRepository(AgentConfigRepository):
    async def get_agent_config_async(
        self,
        agent_id: str,
        **kwargs,
    ) -> AgentConfig | None:
        # File-based implementation
        pass
```

**Implement-specific kwargs**: Trailing `**kwargs` on repository methods let callers pass options that only some backends understand. Implementations should consume only parameters they document (prefer explicit named params before `**kwargs`) and silently ignore the rest. Do not assume a kwarg works across every backend.
```

Keep the existing Benefits / Used for / Note bullets; only refresh the code sample and add the kwargs paragraph.

- [ ] **Step 2: Commit docs**

```bash
git add docs/ARCHITECTURE_PATTERNS.md
git commit -m "$(cat <<'EOF'
docs: document repository implement-specific **kwargs convention

Explain that unused kwargs are ignored and only documented backend options are meaningful.
EOF
)"
```

---

### Task 6: Regression verification

**Files:**
- Verify only (no edits expected)

- [ ] **Step 1: Run kwargs + repository interface tests**

```bash
uv run pytest tests/test_repository_kwargs.py tests/test_repository_base_classes.py -v
```

Expected: PASS

- [ ] **Step 2: Run broader repository suites**

```bash
uv run pytest \
  tests/test_file_agent_config_repository.py \
  tests/test_file_agents_runtime_repository.py \
  tests/test_sqlite_repository.py \
  tests/test_file_model_config_repository.py \
  tests/test_file_tool_config_repository.py \
  tests/test_file_embedding_config_repository.py \
  tests/skills/test_file_skill_config_repository.py \
  -v
```

Expected: PASS

- [ ] **Step 3: Confirm no leftover signature gaps**

```bash
rg -n "async def (update_|get_|list_|delete_).+_async\(" \
  src/fivcplayground/*/types/repositories/*.py \
  src/fivcplayground/agents/types/repositories/*.py
```

Manually verify every public `*_async` repository method in those files ends with `**kwargs` (or is a non-interface helper). If any interface method is missing `**kwargs`, fix and amend only if the last commit is yours and unpushed; otherwise make a new fix commit.

- [ ] **Step 4: Final status check**

```bash
git status
git log --oneline -8
```

Expected: clean worktree for this change set (aside from unrelated untracked files like `.superpowers/`); commits covering tests, agent repos, other ABCs, other File repos, and docs.

---

## Spec Coverage Checklist

| Spec requirement | Task |
|------------------|------|
| Agent ABC `**kwargs` (already done) | Task 2 commit |
| Agent File/Sqlite implementations | Task 2 |
| Models/Tools/Embeddings/Skills ABCs | Task 3 |
| Matching File implementations | Task 4 |
| `ARCHITECTURE_PATTERNS.md` convention | Task 5 |
| Unused kwargs ignored tests (File + Sqlite) | Task 1 + Task 6 |
| No non-repository ABC changes | Out of scope (no task) |
| No new consumed kwargs | Out of scope (no task) |
