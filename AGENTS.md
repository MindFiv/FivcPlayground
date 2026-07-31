# FivcPlayground KNOWLEDGE BASE

**Generated:** 2026-01-26
**Commit:** N/A
**Branch:** N/A

## OVERVIEW
FivcPlayground is an intelligent agent ecosystem built on Strands/LangChain for autonomous tool generation, task assessment, and dynamic agent orchestration with dual backend support.

## STRUCTURE
```
fivcplayground/
├── agents/          # Agent creation and management system
├── backends/        # Pluggable backend implementations (strands, langchain)
├── embeddings/      # Vector database and embedding management
├── models/          # LLM model factories and providers
├── tasks/           # Task execution and workflow orchestration
├── tools/           # Tool management and retrieval system
└── utils/           # Shared utilities (lazy evaluation, directories, args)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Agent creation | `agents/__init__.py` | Factory functions: `create_agent_async()` |
| Model configuration | `models/types/repositories/` | File/SQLite based config storage |
| Tool management | `tools/__init__.py` | Builtin tools and MCP integration |
| Backend switching | `backends/` | Strands (default) vs LangChain |
| Task execution | `tasks/` | Briefing, assessing, planning agents |
| Shared utilities | `utils/` | LazyValue, OutputDir, DefaultKwargs |
| Configuration | `configs/` | Example configurations |
| CLI entry point | `cli.py` | Command-line interface |

## CONVENTIONS

### Repository Pattern
- Dual async/sync interfaces (async primary, sync deprecated)
- Base classes in `*/types/repositories/base.py`
- File-based implementations use YAML/JSON storage
- SQLite implementations for structured data where present

### Factory Pattern
- Async-first: `create_*_async()` primary methods
- Backward compatibility: sync wrappers deprecated but maintained
- Dependency injection: backends and repositories injected

### Domain Organization
- Each domain has: `__init__.py`, `types/`, `types/repositories/`
- Types: Pydantic models + abstract base classes
- Repositories: Data persistence layer with async/await

### Backend Architecture
- Pluggable backends implementing same abstract interfaces
- Strands: Default implementation with message conversion
- LangChain: Alternative with LangChain message mapping

## ANTI-PATTERNS (THIS PROJECT)

### Forbidden Patterns
- Don't use sync methods in new code (deprecated)
- Don't bypass repository pattern for data access
- Don't create agents without factory functions
- Don't implement backends without extending base classes

### Deprecated APIs
- Sync repository methods (use `*_async()` versions)
- Direct database access (use repositories)
- Manual agent instantiation (use factory functions)

## COMMANDS
```bash
# Development
make install        # Install all dependencies
make test           # Run pytest
make lint           # Run ruff linting
make format         # Format code with ruff

# CLI
fivcplayground run Generic --query "task"
fivcplayground clean
```

## NOTES

### Key Architectural Decisions
1. **Async-First**: All new code should use async/await patterns
2. **Repository Abstraction**: Never access files/databases directly
3. **Factory Functions**: Use domain-specific factories for object creation
4. **Plugin Architecture**: Backends are interchangeable implementations

### Critical Files
- `agents/types/repositories/sqlite.py` (549 lines) - Largest file, needs refactoring
- `utils/types/variables.py` - Lazy evaluation proxy pattern

### Development Workflow
1. Use `uv` for dependency management
2. Follow async/await patterns exclusively
3. Extend base classes, don't bypass them
4. Use repository pattern for all data access
5. Test with pytest (async test support included)