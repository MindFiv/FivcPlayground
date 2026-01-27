# AGENTS TYPES

**OVERVIEW**
Core type system for FivcPlayground agent ecosystem with async-first repository pattern and factory-based agent creation.

## STRUCTURE
```
types/
├── base.py              # Core data models and abstract interfaces
├── runnables.py         # Agent runnable wrappers and decorators
├── spans.py             # Context managers for tool and session tracking
└── repositories/
    ├── base.py          # Abstract repository interfaces with async/sync duality
    ├── files.py         # File-based repository implementations
    └── sqlite.py        # SQLite repository implementations
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Agent data models | `base.py` | AgentConfig, AgentRun, AgentRunSession, tool call tracking |
| Runnable interfaces | `base.py` | AgentRunnable abstract class with dual sync/async methods |
| Repository interfaces | `repositories/base.py` | Async-first with deprecated sync wrappers |
| Agent decorators | `runnables.py` | BoundedAgentRunnable, ParameterizedAgentRunnable |
| Context management | `spans.py` | Tool retrieval, session tracking, bundle handling |

## CONVENTIONS

### Async-First Pattern
- Primary methods: `*_async()` versions (e.g., `create_agent_async`)
- Sync methods deprecated but maintained for backward compatibility
- All new code must use async patterns exclusively

### Repository Pattern
- Abstract base classes in `repositories/base.py`
- Dual implementations: file-based (YAML/JSON) and SQLite
- Three-tier data hierarchy: sessions → runs → tool calls

### Factory Pattern
- Agents created via backend factories, not direct instantiation
- Backend implements `AgentBackend` interface with `create_agent_async()`

### Agent Runnable System
- `AgentRunnable` abstract base class defines execution interface
- Decorator pattern for parameterization and bounding
- Event-driven execution with callbacks for streaming

## ANTI-PATTERNS (THIS PROJECT)

### Forbidden Patterns
- Don't use sync repository methods in new code (deprecated)
- Don't bypass repository abstract interfaces
- Don't instantiate agents directly without factories
- Don't implement backends without extending `AgentBackend`

### Deprecated APIs
- All sync repository methods (use `*_async()` versions)
- Direct agent instantiation (use backend factories)
- Manual tool bundle management (use `AgentRunToolSpan`)

### Runtime Management
- Never access repositories directly from agent runnables
- Always use context managers for tool and session tracking
- Don't mix sync and async patterns in the same execution path