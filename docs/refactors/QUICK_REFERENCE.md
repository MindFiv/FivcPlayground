# Interface-Based Architecture: Quick Reference

**Purpose**: Quick lookup guide for developers  
**Status**: Active Reference  
**Last Updated**: 2025-11-14

---

## 🎯 At a Glance

| Aspect | Details |
|--------|---------|
| **Goal** | Enable runtime component swapping via interfaces |
| **Pattern** | Interface-based architecture with DI |
| **Framework** | fivcglue ComponentSite |
| **Timeline** | 10 weeks (5 phases) |
| **Compatibility** | 100% backward compatible |
| **Status** | Design phase complete |

---

## 📚 Document Map

```
START HERE
    │
    ├─ Quick Overview
    │   └─ This document (QUICK_REFERENCE.md)
    │
    ├─ For Architects
    │   ├─ REFACTORING_PLAN.md (overall vision)
    │   ├─ COMPONENT_ARCHITECTURE.md (technical details)
    │   └─ ARCHITECTURE_DIAGRAMS.md (visual reference)
    │
    ├─ For Developers
    │   ├─ IMPLEMENTATION_GUIDE.md (how to implement)
    │   ├─ IMPLEMENTATION_CHECKLIST.md (what to do)
    │   └─ COMPONENT_ARCHITECTURE.md (how it works)
    │
    └─ For Users
        ├─ MIGRATION_GUIDE.md (how to migrate)
        └─ QUICK_REFERENCE.md (quick lookup)
```

---

## 🔑 Key Concepts

### Interface
Contract defining what a component must do
```python
from fivcglue.interfaces import IComponent

class IAgentsRuntimeRepository(IComponent):
    @abstractmethod
    def update_agent(self, agent): ...
```

### Implementation
Concrete class implementing an interface
```python
class SqliteAgentsRuntimeRepository(IAgentsRuntimeRepository):
    def update_agent(self, agent):
        # Implementation
        pass
```

### Dependency Injection
Providing dependencies to components
```python
class ChatManager:
    def __init__(self, repo: IAgentsRuntimeRepository):
        self.repo = repo
```

### Service Locator
Central registry for component resolution
```python
from fivcplayground.utils.di import resolve
repo = resolve(IAgentsRuntimeRepository)
```

---

## 🏗️ Component Areas

| Component | Interface | Implementations | Status |
|-----------|-----------|-----------------|--------|
| Agent Runtime | `IAgentsRuntimeRepository` | File, SQLite | Partial ✅ |
| Model Provider | `IModelProvider` | OpenAI, Ollama | New 🆕 |
| Tools | `IToolsRepository` | Memory, File | New 🆕 |
| Task Runtime | `ITaskRuntimeRepository` | File, SQLite | New 🆕 |
| Embeddings | `IEmbeddingProvider` | OpenAI, Ollama | New 🆕 |
| Config | `IConfigProvider` | YAML, Env, DB | Enhanced 📝 |

---

## 💻 Code Examples

### Example 1: Using Default Implementation

```python
from fivcplayground.utils.di import resolve
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

# Get default implementation
repo = resolve(IAgentsRuntimeRepository)

# Use it
repo.update_agent(agent)
agents = repo.list_agents()
```

### Example 2: Injecting Custom Implementation

```python
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
from fivcplayground.agents.types.repositories import FileAgentsRuntimeRepository

# Create custom implementation
repo = FileAgentsRuntimeRepository()

# Inject into component
chat_manager = ChatManager(agent_runtime_repo=repo)
```

### Example 3: Creating Mock for Testing

```python
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

class MockAgentsRepository(IAgentsRuntimeRepository):
    def __init__(self):
        self.agents = {}
    
    def update_agent(self, agent):
        self.agents[agent.agent_id] = agent
    
    def get_agent(self, agent_id):
        return self.agents.get(agent_id)
    
    # Implement other methods...

# Use in test
def test_chat_manager():
    mock_repo = MockAgentsRepository()
    chat_manager = ChatManager(agent_runtime_repo=mock_repo)
    # Test...
```

### Example 4: Registering Custom Implementation

```python
from fivcplayground.settings import default_component_site
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

class CustomRepository(IAgentsRuntimeRepository):
    # Implementation...
    pass

# Register
default_component_site.register_component(
    IAgentsRuntimeRepository,
    CustomRepository()
)
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Repository selection
export AGENTS_REPOSITORY=sqlite  # or 'file'

# Model provider
export MODEL_PROVIDER=openai  # or 'ollama'

# Tools repository
export TOOLS_REPOSITORY=memory  # or 'file'

# Embedding provider
export EMBEDDING_PROVIDER=openai  # or 'ollama'
```

### YAML Configuration

```yaml
# settings.yaml
components:
  agents_repository:
    type: sqlite
    config:
      db_path: ./agents.db
  
  model_provider:
    type: openai
    config:
      api_key: ${OPENAI_API_KEY}
```

### Programmatic Configuration

```python
from fivcplayground.settings import default_component_site
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
from fivcplayground.agents.types.repositories import FileAgentsRuntimeRepository

default_component_site.register_component(
    IAgentsRuntimeRepository,
    FileAgentsRuntimeRepository()
)
```

---

## 🧪 Testing Patterns

### Unit Test with Mock

```python
def test_chat_manager_with_mock():
    mock_repo = MockAgentsRepository()
    chat_manager = ChatManager(agent_runtime_repo=mock_repo)
    
    # Test
    chat_manager.add_message("Hello")
    assert len(mock_repo.agents) > 0
```

### Integration Test with Real Implementation

```python
def test_chat_manager_integration():
    repo = SqliteAgentsRuntimeRepository(":memory:")
    chat_manager = ChatManager(agent_runtime_repo=repo)
    
    # Test
    chat_manager.add_message("Hello")
    agents = repo.list_agents()
    assert len(agents) > 0
```

### Component Resolution Test

```python
def test_component_resolution():
    from fivcplayground.utils.di import resolve
    from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
    
    repo = resolve(IAgentsRuntimeRepository)
    assert repo is not None
    assert isinstance(repo, IAgentsRuntimeRepository)
```

---

## 🔍 Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Cannot resolve interface" | Not registered | Register in ComponentSite |
| "Type mismatch" | Using concrete class | Use interface type |
| "Mock not working" | Not injected | Pass mock to constructor |
| "Import error" | Wrong module | Check import path |
| "Attribute error" | Missing method | Implement all abstract methods |

---

## 📋 Checklist: Adding New Implementation

- [ ] Create class implementing interface
- [ ] Implement all abstract methods
- [ ] Add type hints
- [ ] Add docstrings
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Register in ComponentSite
- [ ] Update documentation
- [ ] Add configuration support
- [ ] Test with real data

---

## 📋 Checklist: Creating New Interface

- [ ] Define interface class
- [ ] Inherit from `IComponent`
- [ ] Add abstract methods
- [ ] Add comprehensive docstrings
- [ ] Add type hints
- [ ] Document contract/guarantees
- [ ] Create base implementation
- [ ] Write interface tests
- [ ] Update documentation
- [ ] Export in `__init__.py`

---

## 🚀 Quick Start: 5 Minutes

### Step 1: Import Interface
```python
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
```

### Step 2: Resolve Component
```python
from fivcplayground.utils.di import resolve
repo = resolve(IAgentsRuntimeRepository)
```

### Step 3: Use Component
```python
repo.update_agent(agent)
agents = repo.list_agents()
```

### Step 4: Test with Mock
```python
mock_repo = MockAgentsRepository()
chat_manager = ChatManager(agent_runtime_repo=mock_repo)
```

### Step 5: Configure
```bash
export AGENTS_REPOSITORY=file
```

---

## 📊 Implementation Phases

| Phase | Duration | Key Tasks |
|-------|----------|-----------|
| 1 | 2 weeks | Create interfaces, refactor repositories |
| 2 | 2 weeks | Model & embedding providers |
| 3 | 2 weeks | Tools & task repositories |
| 4 | 2 weeks | DI integration |
| 5 | 2 weeks | Testing & documentation |

---

## 🎯 Success Metrics

- ✅ All interfaces defined
- ✅ All implementations refactored
- ✅ 100% backward compatibility
- ✅ DI fully integrated
- ✅ Comprehensive tests
- ✅ Complete documentation
- ✅ No performance regressions
- ✅ Positive community feedback

---

## 📚 Key Files

| File | Purpose |
|------|---------|
| `src/fivcplayground/interfaces/` | Interface definitions |
| `src/fivcplayground/utils/di.py` | DI utilities |
| `src/fivcplayground/settings/__init__.py` | ComponentSite setup |
| `tests/test_interfaces_*.py` | Interface tests |
| `docs/REFACTORING_PLAN.md` | Overall plan |
| `docs/IMPLEMENTATION_GUIDE.md` | Implementation details |

---

## 🔗 Important Links

- [fivcglue GitHub](https://github.com/MindFiv/fivcglue)
- [Dependency Injection](https://en.wikipedia.org/wiki/Dependency_injection)
- [Interface Segregation](https://en.wikipedia.org/wiki/Interface_segregation_principle)
- [Service Locator](https://en.wikipedia.org/wiki/Service_locator_pattern)

---

## 💡 Pro Tips

1. **Always use interfaces in type hints**, not implementations
2. **Inject dependencies** via constructors when possible
3. **Use mocks** for unit testing
4. **Use real implementations** for integration testing
5. **Document assumptions** about which implementation you expect
6. **Test component resolution** in integration tests
7. **Keep implementations stateless** for scalability
8. **Use configuration** for implementation selection

---

## ❓ FAQ

**Q: Do I need to change my code?**  
A: No, old code still works. New code can optionally use interfaces.

**Q: How do I switch implementations?**  
A: Use environment variables, configuration files, or programmatic registration.

**Q: Can I create custom implementations?**  
A: Yes, just implement the interface and register it.

**Q: How do I test with mocks?**  
A: Create a mock class implementing the interface and inject it.

**Q: When will old patterns be removed?**  
A: Not until v1.0.0, with deprecation warnings in v0.3.0.

**Q: Is this production-ready?**  
A: Design is complete. Implementation starts after review.

---

## 📞 Support

- **Questions**: Check documentation
- **Issues**: Report on GitHub
- **Feedback**: Open discussions
- **Contributions**: Submit PRs

---

**Last Updated**: 2025-11-14  
**Status**: Design Complete ✅  
**Next**: Stakeholder Review & Implementation Planning

