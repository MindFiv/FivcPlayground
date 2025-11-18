# FivcPlayground Interface-Based Architecture Refactoring Plan

**Status**: Design Phase  
**Last Updated**: 2025-11-14  
**Target Completion**: Phased implementation over multiple sprints

---

## 📋 Executive Summary

This document outlines a comprehensive refactoring plan to transform FivcPlayground into a flexible, interface-based architecture using fivcglue's dependency injection patterns. The goal is to enable runtime component swapping, supporting multiple implementations for each major component area while maintaining backward compatibility.

**Key Benefits:**
- ✅ Runtime component substitution (e.g., File vs SQLite repositories)
- ✅ Easy addition of new implementations (e.g., multi-tenant repositories)
- ✅ Dependency injection via fivcglue ComponentSite
- ✅ Testability through mock implementations
- ✅ Production-ready extensibility

---

## 🏗️ Architecture Design

### Component Areas to Refactor

1. **AgentsRuntimeRepository** (Already partially done)
   - Interface: `IAgentsRuntimeRepository`
   - Implementations: `FileAgentsRuntimeRepository`, `SqliteAgentsRuntimeRepository`
   - Future: `MultiTenantAgentsRuntimeRepository`, `CloudAgentsRuntimeRepository`

2. **ModelProvider** (New)
   - Interface: `IModelProvider`
   - Implementations: `OpenAIModelProvider`, `OllamaModelProvider`, `LocalModelProvider`
   - Future: `AnthropicModelProvider`, `GeminiModelProvider`

3. **ToolsRepository** (New)
   - Interface: `IToolsRepository`
   - Implementations: `InMemoryToolsRepository`, `FileToolsRepository`, `DatabaseToolsRepository`
   - Future: `RemoteToolsRepository`, `MarketplaceToolsRepository`

4. **TaskRuntimeRepository** (New)
   - Interface: `ITaskRuntimeRepository`
   - Implementations: `FileTaskRuntimeRepository`, `SqliteTaskRuntimeRepository`
   - Future: `DistributedTaskRuntimeRepository`

5. **EmbeddingProvider** (New)
   - Interface: `IEmbeddingProvider`
   - Implementations: `OpenAIEmbeddingProvider`, `OllamaEmbeddingProvider`, `LocalEmbeddingProvider`
   - Future: `HuggingFaceEmbeddingProvider`

6. **ConfigProvider** (Enhance existing)
   - Interface: `IConfigProvider` (extends fivcglue's IConfig)
   - Implementations: `YamlConfigProvider`, `EnvConfigProvider`, `DatabaseConfigProvider`

---

## 📁 Target Project Structure

```
src/fivcplayground/
├── interfaces/                          # NEW: Interface definitions
│   ├── __init__.py
│   ├── repositories.py                  # IAgentsRuntimeRepository, ITaskRuntimeRepository
│   ├── models.py                        # IModelProvider
│   ├── tools.py                         # IToolsRepository
│   ├── embeddings.py                    # IEmbeddingProvider
│   └── config.py                        # IConfigProvider
│
├── agents/
│   ├── types/
│   │   ├── repositories/
│   │   │   ├── base.py                  # REFACTOR: Rename to interfaces.py (move to interfaces/)
│   │   │   ├── files.py                 # FileAgentsRuntimeRepository
│   │   │   └── sqlite.py                # SqliteAgentsRuntimeRepository
│   │   └── ...
│   └── ...
│
├── models/
│   ├── __init__.py                      # REFACTOR: Add provider registry
│   ├── providers/                       # NEW: Provider implementations
│   │   ├── __init__.py
│   │   ├── base.py                      # IModelProvider interface
│   │   ├── openai.py                    # OpenAIModelProvider
│   │   └── ollama.py                    # OllamaModelProvider
│   └── backends/
│       └── ...
│
├── tools/
│   ├── types/
│   │   ├── repositories/                # NEW: Tool repository implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # IToolsRepository interface
│   │   │   ├── memory.py                # InMemoryToolsRepository
│   │   │   └── file.py                  # FileToolsRepository
│   │   └── ...
│   └── ...
│
├── tasks/
│   ├── types/
│   │   ├── repositories/                # NEW: Task repository implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # ITaskRuntimeRepository interface
│   │   │   ├── file.py                  # FileTaskRuntimeRepository
│   │   │   └── sqlite.py                # SqliteTaskRuntimeRepository
│   │   └── ...
│   └── ...
│
├── embeddings/
│   ├── types/
│   │   ├── providers/                   # NEW: Embedding provider implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py                  # IEmbeddingProvider interface
│   │   │   ├── openai.py                # OpenAIEmbeddingProvider
│   │   │   └── ollama.py                # OllamaEmbeddingProvider
│   │   └── ...
│   └── ...
│
├── settings/
│   ├── types/
│   │   ├── config.py                    # REFACTOR: Enhance with provider pattern
│   │   └── ...
│   └── ...
│
├── app/
│   ├── __init__.py                      # REFACTOR: Use DI for component resolution
│   ├── utils/
│   │   ├── chats.py                     # REFACTOR: Accept IAgentsRuntimeRepository
│   │   └── ...
│   └── ...
│
└── utils/
    ├── di.py                            # NEW: Dependency injection utilities
    └── ...
```

---

## 🔄 Interface Definitions

### 1. IAgentsRuntimeRepository (Existing - Enhance)

```python
# src/fivcplayground/interfaces/repositories.py
from abc import abstractmethod
from fivcglue.interfaces import IComponent

class IAgentsRuntimeRepository(IComponent):
    """Interface for agent runtime persistence."""
    
    @abstractmethod
    def update_agent(self, agent: AgentsRuntimeMeta) -> None: ...
    
    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[AgentsRuntimeMeta]: ...
    
    # ... other methods
```

### 2. IModelProvider (New)

```python
# src/fivcplayground/interfaces/models.py
from abc import abstractmethod
from fivcglue.interfaces import IComponent

class IModelProvider(IComponent):
    """Interface for LLM model creation."""
    
    @abstractmethod
    def create_model(self, **kwargs) -> Model: ...
    
    @abstractmethod
    def supports_provider(self, provider: str) -> bool: ...
```

### 3. IToolsRepository (New)

```python
# src/fivcplayground/interfaces/tools.py
from abc import abstractmethod
from fivcglue.interfaces import IComponent

class IToolsRepository(IComponent):
    """Interface for tools storage and retrieval."""
    
    @abstractmethod
    def add_tool(self, tool: Tool) -> None: ...
    
    @abstractmethod
    def get_tool(self, name: str) -> Optional[Tool]: ...
    
    @abstractmethod
    def list_tools(self) -> List[Tool]: ...
```

### 4. ITaskRuntimeRepository (New)

```python
# src/fivcplayground/interfaces/repositories.py
class ITaskRuntimeRepository(IComponent):
    """Interface for task runtime persistence."""
    
    @abstractmethod
    def update_task(self, task: TaskRuntime) -> None: ...
    
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskRuntime]: ...
    
    # ... other methods
```

### 5. IEmbeddingProvider (New)

```python
# src/fivcplayground/interfaces/embeddings.py
from abc import abstractmethod
from fivcglue.interfaces import IComponent

class IEmbeddingProvider(IComponent):
    """Interface for embedding function creation."""
    
    @abstractmethod
    def create_embedding_function(self, **kwargs) -> EmbeddingFunction: ...
    
    @abstractmethod
    def supports_provider(self, provider: str) -> bool: ...
```

---

## 🔧 Dependency Injection Pattern

### ComponentSite Registration

```python
# src/fivcplayground/settings/__init__.py
from fivcglue.implements.utils import ComponentSite
from fivcplayground.interfaces import (
    IAgentsRuntimeRepository,
    IModelProvider,
    IToolsRepository,
    ITaskRuntimeRepository,
    IEmbeddingProvider,
)

def _load_component_site() -> IComponentSite:
    site = ComponentSite()
    
    # Register repositories
    site.register_component(
        IAgentsRuntimeRepository,
        SqliteAgentsRuntimeRepository()
    )
    
    # Register model provider
    site.register_component(
        IModelProvider,
        ModelProviderRegistry()
    )
    
    # Register tools repository
    site.register_component(
        IToolsRepository,
        InMemoryToolsRepository()
    )
    
    # Register task repository
    site.register_component(
        ITaskRuntimeRepository,
        SqliteTaskRuntimeRepository()
    )
    
    # Register embedding provider
    site.register_component(
        IEmbeddingProvider,
        EmbeddingProviderRegistry()
    )
    
    return site
```

---

## 📊 Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
- [ ] Create `interfaces/` module with all interface definitions
- [ ] Refactor `AgentsRuntimeRepository` to use interface pattern
- [ ] Update existing implementations to inherit from interfaces
- [ ] Add interface-based tests

### Phase 2: Model & Embedding Providers (Weeks 3-4)
- [ ] Create `IModelProvider` interface
- [ ] Implement provider registry pattern
- [ ] Refactor model creation to use providers
- [ ] Create `IEmbeddingProvider` interface
- [ ] Implement embedding provider registry

### Phase 3: Tools & Tasks (Weeks 5-6)
- [ ] Create `IToolsRepository` interface
- [ ] Implement multiple tool repository backends
- [ ] Create `ITaskRuntimeRepository` interface
- [ ] Implement task repository backends

### Phase 4: Integration & DI (Weeks 7-8)
- [ ] Integrate ComponentSite into app initialization
- [ ] Update ChatManager to use DI
- [ ] Update CLI to support component selection
- [ ] Add configuration for component selection

### Phase 5: Testing & Documentation (Weeks 9-10)
- [ ] Write comprehensive integration tests
- [ ] Update documentation
- [ ] Create migration guide
- [ ] Performance testing

---

## ✅ Backward Compatibility Strategy

1. **Gradual Migration**: Keep existing factory functions working
2. **Adapter Pattern**: Wrap old code with new interfaces
3. **Feature Flags**: Use environment variables to toggle implementations
4. **Deprecation Warnings**: Warn users about old patterns
5. **Parallel Implementations**: Run old and new side-by-side during transition

---

## 🧪 Testing Strategy

- Unit tests for each interface implementation
- Integration tests for component registration
- Mock implementations for testing
- Backward compatibility tests
- Performance benchmarks

---

## 📝 Next Steps

1. Review and approve this design
2. Create interface definitions in Phase 1
3. Begin refactoring AgentsRuntimeRepository
4. Establish testing patterns
5. Document migration guide for users

