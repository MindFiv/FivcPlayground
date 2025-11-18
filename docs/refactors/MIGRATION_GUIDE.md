# Migration Guide: Interface-Based Architecture

**Purpose**: Guide for users migrating to the new interface-based architecture  
**Status**: Pre-Release  
**Compatibility**: Backward compatible with existing code

---

## 📋 Overview

FivcPlayground is transitioning to an interface-based architecture using fivcglue's dependency injection patterns. This guide helps you understand the changes and migrate your code.

**Key Changes:**
- ✅ New `interfaces/` module with interface definitions
- ✅ Existing implementations now inherit from interfaces
- ✅ Dependency injection via ComponentSite
- ✅ Backward compatible - old code still works
- ✅ New code can use interfaces for flexibility

---

## 🔄 What's Changing

### Before (Old Pattern)

```python
from fivcplayground.agents.types.repositories import (
    SqliteAgentsRuntimeRepository,
)

# Direct instantiation
repo = SqliteAgentsRuntimeRepository()

# Hard-coded dependency
chat_manager = ChatManager(agent_runtime_repo=repo)
```

### After (New Pattern - Optional)

```python
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
from fivcplayground.utils.di import resolve

# Dependency injection
repo = resolve(IAgentsRuntimeRepository)

# Flexible dependency
chat_manager = ChatManager(agent_runtime_repo=repo)
```

**Important**: Old code continues to work! Migration is optional and gradual.

---

## 🚀 Quick Start: Using New Interfaces

### Step 1: Import Interfaces

```python
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
from fivcplayground.interfaces.models import IModelProvider
from fivcplayground.interfaces.tools import IToolsRepository
```

### Step 2: Resolve Components

```python
from fivcplayground.utils.di import resolve

# Get default implementations
agents_repo = resolve(IAgentsRuntimeRepository)
model_provider = resolve(IModelProvider)
tools_repo = resolve(IToolsRepository)
```

### Step 3: Use Components

```python
# Use like before - interface is transparent
agents_repo.update_agent(agent_meta)
model = model_provider.create_model(provider="openai")
tools = tools_repo.list_tools()
```

---

## 🔧 Configuration: Selecting Implementations

### Environment Variables

```bash
# Select repository implementation
export AGENTS_REPOSITORY=sqlite  # or 'file'

# Select model provider
export MODEL_PROVIDER=openai  # or 'ollama'

# Select tools repository
export TOOLS_REPOSITORY=memory  # or 'file'
```

### Configuration File

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
  
  tools_repository:
    type: memory
```

### Programmatic Configuration

```python
from fivcplayground.settings import default_component_site
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
from fivcplayground.agents.types.repositories import FileAgentsRuntimeRepository

# Override default implementation
default_component_site.register_component(
    IAgentsRuntimeRepository,
    FileAgentsRuntimeRepository()
)
```

---

## 📝 Migration Scenarios

### Scenario 1: Using Default Implementations

**No changes needed!** Your existing code works as-is.

```python
# This still works
from fivcplayground.agents.types.repositories import SqliteAgentsRuntimeRepository
repo = SqliteAgentsRuntimeRepository()
```

### Scenario 2: Switching Implementations

**Old way:**
```python
# Had to change code to switch
repo = FileAgentsRuntimeRepository()  # Change code
```

**New way:**
```python
# Just change configuration
export AGENTS_REPOSITORY=file  # Change config
repo = resolve(IAgentsRuntimeRepository)  # Same code
```

### Scenario 3: Custom Implementation

**Create custom implementation:**
```python
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

class CustomAgentsRepository(IAgentsRuntimeRepository):
    def update_agent(self, agent):
        # Custom logic
        pass
    
    # Implement other methods...
```

**Register it:**
```python
from fivcplayground.settings import default_component_site

default_component_site.register_component(
    IAgentsRuntimeRepository,
    CustomAgentsRepository()
)
```

### Scenario 4: Testing with Mocks

**Create mock:**
```python
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

class MockAgentsRepository(IAgentsRuntimeRepository):
    def __init__(self):
        self.agents = {}
    
    def update_agent(self, agent):
        self.agents[agent.agent_id] = agent
    
    # Implement other methods...
```

**Use in tests:**
```python
def test_chat_manager():
    mock_repo = MockAgentsRepository()
    chat_manager = ChatManager(agent_runtime_repo=mock_repo)
    # Test with mock
```

---

## 🔍 Checking Your Code

### Is Your Code Compatible?

✅ **Compatible** - No changes needed:
- Using factory functions (e.g., `create_default_agent()`)
- Using default implementations
- Not directly instantiating repositories

⚠️ **Partially Compatible** - Minor updates recommended:
- Directly instantiating repositories
- Hard-coding implementation choices
- Testing with real implementations

❌ **Incompatible** - Updates required:
- Custom implementations of old base classes
- Monkey-patching implementations
- Relying on internal implementation details

### Migration Checklist

- [ ] Review code for direct repository instantiation
- [ ] Check for hard-coded implementation choices
- [ ] Look for custom implementations
- [ ] Update tests to use mocks
- [ ] Test with new interface-based code
- [ ] Update documentation
- [ ] Deploy and monitor

---

## 🆘 Troubleshooting

### Issue: "Cannot resolve interface"

**Cause**: Component not registered in ComponentSite

**Solution**:
```python
from fivcplayground.settings import default_component_site
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository

# Check if registered
try:
    repo = default_component_site.get_component(IAgentsRuntimeRepository)
except KeyError:
    # Register it
    from fivcplayground.agents.types.repositories import SqliteAgentsRuntimeRepository
    default_component_site.register_component(
        IAgentsRuntimeRepository,
        SqliteAgentsRuntimeRepository()
    )
```

### Issue: "Type mismatch"

**Cause**: Using concrete class instead of interface

**Solution**:
```python
# Wrong
from fivcplayground.agents.types.repositories import SqliteAgentsRuntimeRepository
def my_function(repo: SqliteAgentsRuntimeRepository):
    pass

# Right
from fivcplayground.interfaces.repositories import IAgentsRuntimeRepository
def my_function(repo: IAgentsRuntimeRepository):
    pass
```

### Issue: "Mock not working in tests"

**Cause**: Not injecting mock properly

**Solution**:
```python
# Wrong - still uses real implementation
def test_something():
    chat_manager = ChatManager()  # Uses default

# Right - inject mock
def test_something():
    mock_repo = MockAgentsRepository()
    chat_manager = ChatManager(agent_runtime_repo=mock_repo)
```

---

## 📚 Learning Resources

### Key Concepts

1. **Interface**: Contract defining what a component must do
2. **Implementation**: Concrete class implementing an interface
3. **Dependency Injection**: Providing dependencies to components
4. **Service Locator**: Central registry for component resolution
5. **IComponent**: Base interface from fivcglue

### Documentation

- [REFACTORING_PLAN.md](./REFACTORING_PLAN.md) - Overall architecture design
- [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - Implementation details
- [COMPONENT_ARCHITECTURE.md](./COMPONENT_ARCHITECTURE.md) - Component interactions
- [fivcglue Documentation](https://github.com/MindFiv/fivcglue) - DI framework

---

## 🎯 Best Practices

1. **Use Interfaces**: Type hints with interfaces, not implementations
2. **Inject Dependencies**: Pass dependencies to constructors
3. **Use Service Locator as Fallback**: Only when DI not possible
4. **Mock in Tests**: Use mock implementations for testing
5. **Document Assumptions**: Explain which implementation you expect
6. **Version Your APIs**: Consider backward compatibility
7. **Test Integration**: Test with real implementations too

---

## 📞 Support

- **Issues**: Report on GitHub
- **Questions**: Check documentation
- **Contributions**: Submit PRs
- **Feedback**: Open discussions

---

## 🔄 Rollout Timeline

- **v0.2.0**: Interfaces available, old code still works
- **v0.3.0**: Interfaces recommended, deprecation warnings
- **v1.0.0**: Interfaces required, old patterns removed

**Current Version**: v0.1.0 (Pre-interface release)

