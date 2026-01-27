# AGENTS

**OVERVIEW**
Agent creation and management system with pluggable backend integration and async-first factory pattern.

## STRUCTURE
```
agents/
├── __init__.py           # Factory functions and public API
└── types/
    ├── base.py           # Core data models and abstract interfaces
    ├── runnables.py      # Agent runnable wrappers and decorators
    ├── spans.py          # Context managers for tool and session tracking
    └── repositories/
        ├── base.py       # Abstract repository interfaces
        ├── files.py      # File-based repository implementations
        └── sqlite.py     # SQLite repository implementations
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Agent creation | `__init__.py` | `create_agent_async()` factory function |
| Agent configuration | `types/base.py` | AgentConfig, AgentRun, AgentRunSession models |
| Backend interface | `types/base.py` | AgentBackend abstract class |
| Repository pattern | `types/repositories/` | Async-first with dual implementations |
| Runnable decorators | `types/runnables.py` | BoundedAgentRunnable, ParameterizedAgentRunnable |

## CONVENTIONS

### Factory Pattern
- Agents created exclusively via `create_agent_async()` factory
- Backend implements `AgentBackend.create_agent_async()` interface
- Never instantiate agents directly

### Async-First Design
- Primary factory: `create_agent_async()`
- Sync wrapper deprecated but maintained
- All repository methods async-first

### Backend Integration
- Pluggable backends via `AgentBackend` interface
- Model backend injection for LLM provider flexibility
- Tool retriever integration for dynamic tool selection

### Repository Pattern
- Three-tier hierarchy: sessions → runs → tool calls
- Abstract interfaces with file/SQLite implementations
- Async methods primary, sync deprecated

## ANTI-PATTERNS (THIS PROJECT)

### Forbidden Patterns
- Don't use sync `create_agent()` in new code
- Don't instantiate agents without factory functions
- Don't bypass repository abstract interfaces
- Don't implement backends without extending AgentBackend

### Deprecated APIs
- Sync factory method `create_agent()`
- All sync repository methods
- Direct agent instantiation