# Interface-Based Architecture Implementation Guide

**Purpose**: Step-by-step guide for implementing the interface-based refactoring  
**Target Audience**: Developers implementing the refactoring  
**Status**: Active Implementation Guide

---

## 🎯 Core Principles

1. **Interface First**: Define interfaces before implementations
2. **IComponent Pattern**: All interfaces inherit from `fivcglue.interfaces.IComponent`
3. **Dependency Injection**: Use ComponentSite for registration and resolution
4. **Backward Compatibility**: Maintain existing APIs during transition
5. **Testability**: Design for easy mocking and testing

---

## 📋 Phase 1: Foundation Setup

### Step 1.1: Create Interfaces Module

```bash
mkdir -p src/fivcplayground/interfaces
touch src/fivcplayground/interfaces/__init__.py
```

### Step 1.2: Define Repository Interfaces

**File**: `src/fivcplayground/interfaces/repositories.py`

```python
from abc import abstractmethod
from typing import Optional, List
from fivcglue.interfaces import IComponent
from fivcplayground.agents.types import (
    AgentsRuntimeMeta,
    AgentsRuntime,
    AgentsRuntimeToolCall,
)

class IAgentsRuntimeRepository(IComponent):
    """Interface for agent runtime persistence."""
    
    @abstractmethod
    def update_agent(self, agent: AgentsRuntimeMeta) -> None:
        """Create or update agent metadata."""
        ...
    
    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[AgentsRuntimeMeta]:
        """Retrieve agent metadata by ID."""
        ...
    
    @abstractmethod
    def list_agents(self) -> List[AgentsRuntimeMeta]:
        """List all agents."""
        ...
    
    @abstractmethod
    def delete_agent(self, agent_id: str) -> None:
        """Delete agent and all associated data."""
        ...
    
    @abstractmethod
    def update_agent_runtime(
        self, agent_id: str, agent_runtime: AgentsRuntime
    ) -> None:
        """Create or update agent runtime."""
        ...
    
    @abstractmethod
    def get_agent_runtime(
        self, agent_id: str, agent_run_id: str
    ) -> Optional[AgentsRuntime]:
        """Retrieve agent runtime."""
        ...
    
    @abstractmethod
    def list_agent_runtimes(self, agent_id: str) -> List[AgentsRuntime]:
        """List all runtimes for an agent."""
        ...
    
    @abstractmethod
    def delete_agent_runtime(self, agent_id: str, agent_run_id: str) -> None:
        """Delete agent runtime and tool calls."""
        ...
    
    @abstractmethod
    def update_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_call: AgentsRuntimeToolCall
    ) -> None:
        """Create or update tool call."""
        ...
    
    @abstractmethod
    def get_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_use_id: str
    ) -> Optional[AgentsRuntimeToolCall]:
        """Retrieve tool call."""
        ...
    
    @abstractmethod
    def list_agent_runtime_tool_calls(
        self, agent_id: str, agent_run_id: str
    ) -> List[AgentsRuntimeToolCall]:
        """List all tool calls for a runtime."""
        ...
    
    @abstractmethod
    def delete_agent_runtime_tool_call(
        self, agent_id: str, agent_run_id: str, tool_use_id: str
    ) -> None:
        """Delete tool call."""
        ...
```

### Step 1.3: Update Existing Implementations

**File**: `src/fivcplayground/agents/types/repositories/base.py`

```python
# CHANGE: Import from interfaces instead of defining locally
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

# Keep the class for backward compatibility
class AgentsRuntimeRepository(IAgentsRuntimeRepository):
    """Backward compatibility alias for IAgentsRuntimeRepository."""
    pass
```

**File**: `src/fivcplayground/agents/types/repositories/files.py`

```python
# CHANGE: Inherit from interface
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

class FileAgentsRuntimeRepository(IAgentsRuntimeRepository):
    """File-based implementation of IAgentsRuntimeRepository."""
    # ... existing implementation
```

**File**: `src/fivcplayground/agents/types/repositories/sqlite.py`

```python
# CHANGE: Inherit from interface
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

class SqliteAgentsRuntimeRepository(IAgentsRuntimeRepository):
    """SQLite-based implementation of IAgentsRuntimeRepository."""
    # ... existing implementation
```

---

## 🔌 Phase 2: Model Provider Interface

### Step 2.1: Create Model Provider Interface

**File**: `src/fivcplayground/interfaces/models.py`

```python
from abc import abstractmethod
from typing import Any
from fivcglue.interfaces import IComponent

class IModelProvider(IComponent):
    """Interface for LLM model creation."""
    
    @abstractmethod
    def create_model(self, **kwargs) -> Any:
        """Create a model instance."""
        ...
    
    @abstractmethod
    def supports_provider(self, provider: str) -> bool:
        """Check if this provider supports the given provider name."""
        ...
```

### Step 2.2: Create Provider Registry

**File**: `src/fivcplayground/models/providers/registry.py`

```python
from typing import Dict, Callable
from fivcplayground.interfaces.models import IModelProvider

class ModelProviderRegistry(IModelProvider):
    """Registry for model providers."""
    
    def __init__(self):
        self.providers: Dict[str, Callable] = {}
    
    def register(self, name: str, factory: Callable) -> None:
        """Register a model provider factory."""
        self.providers[name] = factory
    
    def create_model(self, provider: str = "openai", **kwargs):
        """Create a model using registered provider."""
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}")
        return self.providers[provider](**kwargs)
    
    def supports_provider(self, provider: str) -> bool:
        """Check if provider is registered."""
        return provider in self.providers
```

---

## 🛠️ Phase 3: Dependency Injection Setup

### Step 3.1: Update Settings Module

**File**: `src/fivcplayground/settings/__init__.py`

```python
# Add to existing _load_component_site function
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
from fivcplayground.agents.types.repositories import (
    SqliteAgentsRuntimeRepository,
)

def _load_component_site() -> IComponentSite:
    site = ComponentSite()
    
    # ... existing code ...
    
    # Register default implementations
    site.register_component(
        IAgentsRuntimeRepository,
        SqliteAgentsRuntimeRepository()
    )
    
    return site
```

### Step 3.2: Create DI Utilities

**File**: `src/fivcplayground/utils/di.py`

```python
from typing import Type, TypeVar, Optional
from fivcglue.interfaces import IComponentSite
from fivcplayground.settings import default_component_site

T = TypeVar('T')

def resolve(interface: Type[T]) -> T:
    """Resolve a component from the default component site."""
    site = default_component_site
    return site.get_component(interface)

def resolve_from_site(
    site: IComponentSite, interface: Type[T]
) -> T:
    """Resolve a component from a specific component site."""
    return site.get_component(interface)
```

---

## 🧪 Testing Patterns

### Mock Implementation Example

```python
# tests/mocks/mock_agents_repository.py
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

class MockAgentsRuntimeRepository(IAgentsRuntimeRepository):
    """Mock implementation for testing."""
    
    def __init__(self):
        self.agents = {}
        self.runtimes = {}
    
    def update_agent(self, agent):
        self.agents[agent.agent_id] = agent
    
    def get_agent(self, agent_id):
        return self.agents.get(agent_id)
    
    # ... implement other methods
```

### Integration Test Example

```python
# tests/test_di_integration.py
from fivcplayground.settings import default_component_site
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

def test_agents_repository_resolution():
    repo = default_component_site.get_component(IAgentsRuntimeRepository)
    assert repo is not None
    assert isinstance(repo, IAgentsRuntimeRepository)
```

---

## 📝 Migration Checklist

- [ ] Create interfaces module
- [ ] Define all interface classes
- [ ] Update existing implementations
- [ ] Create provider registries
- [ ] Setup ComponentSite registration
- [ ] Create DI utilities
- [ ] Write integration tests
- [ ] Update documentation
- [ ] Update CLI for component selection
- [ ] Performance testing
- [ ] User migration guide

---

## 🚀 Rollout Strategy

1. **Internal Testing**: Test with mock implementations
2. **Staged Rollout**: Deploy to staging environment
3. **Beta Release**: Release with feature flag
4. **Full Release**: Make default in next major version
5. **Deprecation**: Mark old patterns as deprecated

---

## 📚 References

- [fivcglue Documentation](https://github.com/MindFiv/fivcglue)
- [Dependency Injection Pattern](https://en.wikipedia.org/wiki/Dependency_injection)
- [Interface Segregation Principle](https://en.wikipedia.org/wiki/Interface_segregation_principle)

