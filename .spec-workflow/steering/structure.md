# Project Structure

## Directory Organization

```
FivcAdvisor/
├── src/fivcadvisor/          # Main source code (src layout)
│   ├── agents/               # Agent creation and management
│   │   ├── __init__.py       # Agent factory functions and exports
│   │   └── types/            # Agent-related types and utilities
│   │       ├── __init__.py   # Type exports
│   │       ├── conversations.py  # Conversation management
│   │       └── retrievers.py     # Agent retrieval and creation decorators
│   │
│   ├── app/                  # Streamlit web interface
│   │   ├── __init__.py       # Main app entry point
│   │   ├── components/       # Reusable UI components
│   │   ├── views/            # Page views (chat, settings, tasks)
│   │   │   ├── chat.py       # Chat interface
│   │   │   ├── settings.py   # Settings page
│   │   │   └── tasks.py      # Task management page
│   │   ├── messages.py       # Message rendering and callbacks
│   │   ├── sessions.py       # Session management
│   │   └── tools.py          # Tool callbacks for UI
│   │
│   ├── embeddings/           # Vector database and embeddings
│   │   ├── __init__.py       # Embeddings exports
│   │   └── types/            # Embedding database types
│   │       └── db.py         # ChromaDB wrapper
│   │
│   ├── settings/             # Configuration management
│   │   ├── __init__.py       # Settings exports and lazy loading
│   │   └── types.py          # SettingsConfig class
│   │
│   ├── tasks/                # Task execution and orchestration
│   │   ├── __init__.py       # Task execution functions
│   │   └── types/            # Task-related types
│   │       ├── base.py       # TaskRuntime and TaskRuntimeStep models
│   │       ├── managers.py   # TaskManager for task lifecycle
│   │       ├── monitors.py   # TaskMonitor for hook-based execution tracking
│   │       └── repositories/ # Task runtime persistence
│   │           ├── __init__.py       # Repository base classes
│   │           └── files.py          # FileTaskRuntimeRepository implementation
│   │
│   ├── tools/                # Tool management and retrieval
│   │   ├── __init__.py       # Tool registration and exports
│   │   └── types/            # Tool-related types
│   │       ├── configs.py    # ToolsConfig for MCP integration
│   │       └── retrievers.py # ToolsRetriever for semantic search
│   │
│   ├── utils/                # Utility functions
│   │   ├── __init__.py       # Utility exports
│   │   ├── directories.py    # Directory management
│   │   └── variables.py      # Lazy loading and variable utilities
│   │
│   ├── __init__.py           # Package exports
│   ├── cli.py                # Typer CLI entry point
│   ├── models.py             # LLM model factories
│   └── schemas.py            # Pydantic data schemas
│
├── tests/                    # Test suite (mirrors src structure)
│   ├── test_agent_creator.py
│   ├── test_conversation_manager.py
│   ├── test_embeddings.py
│   ├── test_execution_integration.py
│   ├── test_file_task_runtime_repository.py
│   ├── test_repository_integration.py
│   ├── test_schemas.py
│   ├── test_settings.py
│   ├── test_task_manager.py
│   ├── test_task_monitor.py
│   ├── test_tools_config.py
│   ├── test_tools_retriever.py
│   └── test_utils.py
│
├── configs/                  # Configuration examples
│   ├── mcp.yaml.example      # MCP tool configuration template
│   └── settings.yaml.example # Application settings template
│
├── docs/                     # Documentation
│   ├── README.md             # Documentation index
│   ├── DESIGN.md             # System design and architecture
│   ├── DEPENDENCIES.md       # Dependency management guide
│   └── WEB_INTERFACE.md      # Web interface documentation
│
├── examples/                 # Usage examples
│   ├── agents/               # Agent usage examples
│   ├── tasks/                # Task execution examples
│   └── tools/                # Tool usage examples
│
├── repl_state/               # REPL state persistence
│   └── repl_state.pkl        # Pickled REPL state
│
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore patterns
├── Makefile                  # Common development commands
├── pyproject.toml            # Project metadata and dependencies
├── README.md                 # Main project README
└── uv.lock                   # Dependency lock file
```

**Organizational Principles:**
- **Src Layout**: Clean separation between source (`src/`) and package root
- **Feature-based Modules**: Each top-level module represents a major feature (agents, tools, tasks, etc.)
- **Types Subdirectories**: Complex modules have `types/` subdirectories for implementation details
- **Flat Top-level**: Core abstractions (models, schemas, cli) at package root for easy access

## Naming Conventions

### Files
- **Modules**: `snake_case` (e.g., `conversation_manager.py`, `task_tracer.py`)
- **Package Markers**: `__init__.py` for all packages and subpackages
- **Tests**: `test_<module_name>.py` (e.g., `test_agent_creator.py`)
- **Configuration**: `<name>.yaml` or `<name>.yaml.example`
- **Documentation**: `UPPERCASE.md` for major docs, `lowercase.md` for guides

### Code
- **Classes/Types**: `PascalCase` (e.g., `AgentsRetriever`, `TaskManager`, `SettingsConfig`)
- **Functions/Methods**: `snake_case` (e.g., `create_default_agent`, `run_tooling_task`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MODEL`, `MAX_RETRIES`)
- **Variables**: `snake_case` (e.g., `tools_retriever`, `agent_config`)
- **Private Members**: Leading underscore `_private_method`, `_internal_var`
- **Decorators**: `snake_case` (e.g., `@agent_creator`)

### Special Patterns
- **Factory Functions**: `create_<name>` (e.g., `create_default_agent`, `create_chat_model`)
- **Lazy Values**: `<name>_config` for lazy-loaded configurations
- **Retrievers**: `<name>_retriever` for retrieval classes
- **Managers**: `<Name>Manager` for lifecycle management classes
- **Monitors**: `<Name>Monitor` for execution tracking classes
- **Repositories**: `<Name>Repository` for data persistence abstractions
- **Base Models**: `base.py` for core data models in a module

## Import Patterns

### Import Order (PEP 8 Compliant)
1. **Standard library imports** (e.g., `os`, `typing`)
2. **Third-party imports** (e.g., `strands`, `streamlit`, `pydantic`)
3. **Local application imports** (e.g., `from fivcadvisor import agents`)
4. **Relative imports** (e.g., `from .types import AgentsRetriever`)

### Module Organization

```python
# Example from agents/__init__.py
__all__ = [
    "create_default_agent",
    "create_tooling_agent",
    # ... explicit exports
]

# Standard library
from typing import cast, List, Optional, Callable

# Third-party
from strands.agent import Agent
from strands.multiagent import Swarm

# Local absolute imports
from fivcadvisor import models, tools, utils

# Relative imports
from fivcadvisor.agents.types import (
    agents_creator,
    AgentsRetriever,
    ToolFilteringConversationManager,
)
```

### Import Patterns
- **Absolute imports preferred**: `from fivcadvisor.agents import create_default_agent`
- **Relative imports for types**: `from .types import SomeType` within same package
- **Lazy imports**: Import heavy dependencies inside functions when needed
- **Explicit exports**: Use `__all__` to define public API in `__init__.py`

## Code Structure Patterns

### Module/File Organization
```python
# Standard pattern for module files:

# 1. Module docstring (if applicable)
"""
Module description and purpose.
"""

# 2. Exports declaration
__all__ = ["PublicClass", "public_function"]

# 3. Imports (ordered as above)
import os
from typing import Optional

from third_party import SomeClass

from fivcadvisor import utils
from .types import InternalType

# 4. Constants and configuration
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# 5. Type definitions (if needed)
ConfigDict = dict[str, Any]

# 6. Main implementation (classes, functions)
class PublicClass:
    """Public class with docstring."""
    pass

def public_function():
    """Public function with docstring."""
    pass

# 7. Private/helper functions
def _private_helper():
    """Internal helper function."""
    pass
```

### Class Organization
```python
class ExampleClass:
    """Class docstring explaining purpose."""
    
    # 1. Class variables
    class_var: ClassVar[str] = "value"
    
    # 2. __init__ and initialization
    def __init__(self, param: str):
        self.param = param
        self._private_state = None
    
    # 3. Public methods (alphabetically or by importance)
    def public_method(self) -> str:
        """Public method with docstring."""
        return self._private_method()
    
    # 4. Properties
    @property
    def computed_value(self) -> int:
        """Property with docstring."""
        return len(self.param)
    
    # 5. Private methods
    def _private_method(self) -> str:
        """Internal implementation."""
        return self.param.upper()
    
    # 6. Special methods (if not __init__)
    def __repr__(self) -> str:
        return f"ExampleClass(param={self.param!r})"
```

### Function Organization
```python
def example_function(
    required_param: str,
    optional_param: Optional[int] = None,
    **kwargs: Any,
) -> Result:
    """
    Function docstring with description.
    
    Args:
        required_param: Description of required parameter
        optional_param: Description of optional parameter
        **kwargs: Additional keyword arguments
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When validation fails
    """
    # 1. Input validation
    if not required_param:
        raise ValueError("required_param cannot be empty")
    
    # 2. Setup and initialization
    config = _load_config()
    
    # 3. Core logic
    result = _process_data(required_param, config)
    
    # 4. Post-processing
    result = _validate_result(result)
    
    # 5. Return
    return result
```

## Code Organization Principles

1. **Single Responsibility**: Each module/class/function has one clear purpose
   - `agents/` only handles agent creation and management
   - `tools/` only handles tool retrieval and configuration
   - `models.py` only contains model factory functions

2. **Modularity**: Code organized into reusable, independent modules
   - Each major feature is a separate package
   - Types subdirectories contain implementation details
   - Utilities are centralized in `utils/`

3. **Explicit Public API**: Use `__all__` to define what's exported
   - Every `__init__.py` declares its public interface
   - Internal implementation in `types/` subdirectories
   - Clear separation between public and private

4. **Lazy Loading**: Defer expensive initialization
   - Settings loaded lazily via `create_lazy_value`
   - Tools registered on first access
   - Models created on demand

5. **Decorator-based Factories**: Clean registration pattern
   - `@agent_creator` decorator for agent factories
   - Automatic registration in retrievers
   - Type-safe factory functions

6. **Repository Pattern**: Abstraction for data persistence
   - Abstract base classes define interfaces (e.g., `TaskRuntimeRepository`)
   - Concrete implementations in subdirectories (e.g., `repositories/files.py`)
   - Dependency injection for flexibility and testability
   - Clear separation between domain models and persistence

## Module Boundaries

### Core vs Extensions
- **Core**: `agents/`, `tools/`, `tasks/types/base.py`, `models.py`, `schemas.py`, `settings/`
  - Stable, well-tested, minimal dependencies
  - Changes require careful consideration
  - Includes core data models and abstractions

- **Extensions**: `app/`, `tasks/types/repositories/`, `embeddings/`
  - Can evolve independently
  - Optional features that depend on core
  - Concrete implementations of core abstractions

### Public API vs Internal
- **Public API**: Exported via `__all__` in `__init__.py`
  - Stable interface for users
  - Documented and tested
  - Example: `create_default_agent()`, `ToolsRetriever`

- **Internal**: `types/` subdirectories and `_private` functions
  - Implementation details
  - Can change without notice
  - Example: `_load_config()`, internal classes

### Dependency Direction
```
┌─────────────────────────────────────────┐
│              CLI / App                   │  ← User-facing interfaces
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Agents / Tasks / Tools              │  ← High-level orchestration
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Models / Schemas / Settings         │  ← Core abstractions
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Utils / Embeddings                  │  ← Low-level utilities
└─────────────────────────────────────────┘
```

**Rules:**
- Higher layers can depend on lower layers
- Lower layers NEVER depend on higher layers
- Circular dependencies are forbidden
- Use dependency injection for flexibility

## Code Size Guidelines

### File Size
- **Target**: 100-300 lines per file
- **Maximum**: 500 lines (consider splitting if exceeded)
- **Exceptions**: `__init__.py` can be larger for exports

### Function/Method Size
- **Target**: 10-30 lines per function
- **Maximum**: 50 lines (consider extracting helpers)
- **Single responsibility**: One function, one purpose

### Class Complexity
- **Target**: 5-15 methods per class
- **Maximum**: 20 methods (consider composition)
- **Cohesion**: All methods should relate to class purpose

### Nesting Depth
- **Maximum**: 3 levels of nesting
- **Prefer**: Early returns and guard clauses
- **Extract**: Complex nested logic into helper functions

## Task Execution Architecture

### Task Runtime Components
The task execution system is built on four main components:

1. **Data Models** (`tasks/types/base.py`)
   - `TaskRuntime`: Overall task execution state with computed fields (task_id, duration, is_completed)
   - `TaskRuntimeStep`: Individual agent execution step with computed fields (agent_id, duration, is_running, is_completed)
   - `TaskStatus`: Execution status enumeration (from Strands)
   - Synchronization methods: `sync()`, `sync_status()`, `sync_started_at()`, `sync_completed_at()`

2. **Monitoring** (`tasks/types/monitors.py`)
   - `TaskMonitor`: Hook-based execution tracking (requires runtime_repo)
   - `TaskMonitorManager`: Centralized task lifecycle management
   - Integrates with Strands' hook system
   - Required persistence through repository pattern
   - Real-time step updates via callbacks

3. **Persistence** (`tasks/types/repositories/`)
   - `TaskRuntimeRepository`: Abstract base class
   - `FileTaskRuntimeRepository`: File-based implementation
   - Hierarchical directory structure with JSON files
   - Human-readable and version-control friendly

4. **Management** (`tasks/types/monitors.py`)
   - `TaskMonitorManager`: Manages multiple tasks with centralized monitoring
   - Automatic task creation with planning integration
   - Task querying and filtering by status
   - Unified persistence through repository

### Task Execution Flow
```
User Request
    ↓
TaskMonitorManager.create_task()
    ↓
Planning Task (if needed)
    ↓
TaskMonitor (hooks into Strands)
    ↓
Agent/MultiAgent Execution
    ↓
TaskRuntimeRepository (required persistence)
    ↓
Task Results
```

### Repository Pattern Implementation
```
tasks/types/repositories/
├── __init__.py           # Abstract TaskRuntimeRepository base class
└── files.py              # FileTaskRuntimeRepository implementation

Storage Structure:
/<output_dir>/
└── task_<task_id>/
    ├── task.json         # Task metadata
    └── steps/
        ├── step_<step_id>.json
        └── step_<step_id>.json
```

## Web Interface Structure

### Streamlit App Organization
```
src/fivcadvisor/app/
├── __init__.py           # Main app entry point and routing
├── components/           # Reusable UI components
│   └── __init__.py       # Component exports
├── views/                # Page views (one per page)
│   ├── __init__.py       # View exports
│   ├── chat.py           # Chat interface page
│   ├── settings.py       # Settings page
│   └── tasks.py          # Task management page
├── messages.py           # Message rendering and callbacks
├── sessions.py           # Session state management
└── tools.py              # Tool execution callbacks
```

### Separation of Concerns
- **App isolated from core**: Web UI doesn't affect CLI or library usage
- **Own entry point**: `fivcadvisor web` command launches Streamlit
- **Minimal dependencies**: App only imports from core modules
- **Can be disabled**: Core functionality works without web interface

### View Pattern
Each view file follows this pattern:
```python
def render():
    """Render the page view."""
    st.title("Page Title")
    
    # Get shared session state
    session = st.session_state.chat_session
    
    # Render UI components
    # Handle user interactions
    # Update state and rerun if needed
```

## Documentation Standards

### Docstring Style
- **Format**: Google-style docstrings
- **Required for**: All public classes, functions, and methods
- **Optional for**: Private functions (but encouraged)

### Example Docstring
```python
def create_agent(name: str, tools: List[Tool]) -> Agent:
    """
    Create a new agent with specified tools.
    
    Args:
        name: Human-readable name for the agent
        tools: List of tools the agent can use
    
    Returns:
        Configured Agent instance ready for execution
    
    Raises:
        ValueError: If name is empty or tools list is invalid
    
    Example:
        >>> agent = create_agent("Assistant", [calculator, search])
        >>> result = agent.run("What is 2+2?")
    """
    pass
```

### Module Documentation
- **README.md**: Every major module should have usage examples
- **Inline comments**: Explain complex logic and non-obvious decisions
- **Type hints**: All function signatures should have type annotations
- **Examples**: Provide usage examples in docstrings or examples/

### Documentation Files
- **docs/DESIGN.md**: System architecture and design decisions
- **docs/DEPENDENCIES.md**: Dependency management and installation
- **docs/WEB_INTERFACE.md**: Web interface usage guide
- **README.md**: Quick start and overview

