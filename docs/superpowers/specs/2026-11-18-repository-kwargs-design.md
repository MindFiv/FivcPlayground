# Repository Interface `**kwargs` Extension

**Date:** 2026-11-18  
**Status:** Approved for planning  
**Scope:** All config/run repository ABCs and their implementations

## Goal

Extend repository interfaces so callers can pass **implementation-specific** keyword arguments through the shared ABC, without forcing every backend to declare the same parameters. Existing File/Sqlite behavior stays unchanged until an implementation documents and consumes a given kwarg.

## Decisions

| Topic | Choice |
|-------|--------|
| Purpose | Pure contract extension (A), not landing concrete kwargs yet |
| Breadth | Unify all repository ABCs (C): agents, models, tools, embeddings, skills |
| Unknown kwargs | Hybrid (C): implementations consume documented params only; everything else is silently ignored |
| Approach | Mechanical signature alignment (Option 1) |

## Out of Scope

- Non-repository ABCs (`AgentBackend`, `ToolBackend`, `AgentRunnable`, retrievers, etc.)
- Adding new behavior or named kwargs that File/Sqlite actually use in this change
- TypedDict / Protocol schemas for kwargs (deferred until a concrete param exists)

## Contract

1. Every abstract repository method accepts trailing `**kwargs`.
2. Concrete implementations mirror `**kwargs` in their signatures so callers typed against the ABC (or the concrete class) can pass extras without `TypeError`.
3. Implementations that do not use a kwarg simply ignore it (no raise, no warning).
4. When an implementation starts consuming kwargs, it should:
   - Prefer explicit named parameters before `**kwargs` (e.g. `*, conn=None, **kwargs`)
   - Document those parameters on the implementation class/method
5. Callers must not assume kwargs work across all backends—only what the target implementation documents.

## Files to Update

### Interfaces (`**/types/repositories/base.py`)

- `agents` — `AgentConfigRepository`, `AgentRunRepository` (already updated)
- `models` — `ModelConfigRepository` (extend beyond `list_*`)
- `tools` — `ToolConfigRepository` (extend beyond `list_*`)
- `embeddings` — `EmbeddingConfigRepository` (extend beyond `list_*`)
- `skills` — `SkillConfigRepository` (add to all methods)

### Implementations

- `agents/types/repositories/files.py` — File agent config + run repos
- `agents/types/repositories/sqlite.py` — Sqlite agent run repo
- `models/types/repositories/files.py`
- `tools/types/repositories/files.py`
- `embeddings/types/repositories/files.py`
- `skills/types/repositories/files.py`

### Documentation

- `docs/ARCHITECTURE_PATTERNS.md` — update repository pattern example signatures and add the implement-specific kwargs convention note
- Do not change `CLAUDE.md` / `AGENTS.md` in this workstream unless a code comment elsewhere already points callers there for repository contracts

### Tests

- Update `tests/test_repository_base_classes.py` (and sibling repo tests if present) so complete stub implementations accept `**kwargs`
- Add focused cases: calling File/Sqlite methods with an unused kwarg does not raise and returns the same result as without it
- Existing callers that omit kwargs need no changes

## Success Criteria

- All repository ABC methods and matching implementations accept `**kwargs`
- No behavioral change for current call sites
- Docs state the implement-specific / silent-ignore convention
- Tests cover “extra kwargs are ignored” for at least one File and one Sqlite path

## Non-Goals Recap

Do not expand this pattern to backends or runtime interfaces in the same change. Revisit later if those surfaces show the same “per-backend options through a shared ABC” need.
