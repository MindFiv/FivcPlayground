# Backend Selection Guide

FivcPlayground supports two agent frameworks: **Strands** (default) and **LangChain** (alternative). This guide explains how to choose and switch between them.

## 🎯 Quick Comparison

| Feature | Strands | LangChain |
|---------|---------|-----------|
| **Status** | Default | Alternative |
| **Framework** | strands-agents | langchain-core |
| **Agent Orchestration** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Ecosystem** | Focused | Broad |
| **Tool Integration** | Native | Via adapters |
| **Performance** | Optimized | General-purpose |
| **Learning Curve** | Moderate | Moderate |

## 🚀 Switching Backends

Backend selection is done explicitly when creating backend instances. Both backends are available and can be used simultaneously in different parts of your application.

### Using Strands Backend (Default)

```python
from fivcplayground.backends.strands import (
    StrandsAgentBackend,
    StrandsModelBackend,
    StrandsToolBackend,
)

agent_backend = StrandsAgentBackend()
model_backend = StrandsModelBackend()
tool_backend = StrandsToolBackend()
```

### Using LangChain Backend

```python
from fivcplayground.backends.langchain import (
    LangchainAgentBackend,
    LangchainModelBackend,
    LangchainToolBackend,
)

agent_backend = LangchainAgentBackend()
model_backend = LangchainModelBackend()
tool_backend = LangchainToolBackend()
```

### Verify Dependencies

Both backends are installed by default. Verify with:

```bash
# Check Strands
python -c "import strands; print('Strands OK')"

# Check LangChain
python -c "import langchain_core; print('LangChain OK')"
```

## 📋 When to Use Each Backend

### Use **Strands** if:
- You want the default, tested configuration
- You need optimized agent orchestration
- You're building multi-agent systems
- You want the best performance for agents

### Use **LangChain** if:
- You need broader ecosystem integration
- You want to use LangChain-specific tools
- You're integrating with LangChain projects
- You need specific LangChain features

## 🔧 Implementation Details

### Backend Architecture

Each backend is implemented as a separate module with consistent interfaces:

- **Agents**: `src/fivcplayground/backends/langchain/agents.py` and `src/fivcplayground/backends/strands/agents.py`
- **Models**: `src/fivcplayground/backends/langchain/models.py` and `src/fivcplayground/backends/strands/models.py`
- **Tools**: `src/fivcplayground/backends/langchain/tools.py` and `src/fivcplayground/backends/strands/tools.py`

### Using Multiple Backends

You can use different backends for different components in the same application:

```python
from fivcplayground.backends.strands import StrandsAgentBackend
from fivcplayground.backends.langchain import LangchainModelBackend

# Use Strands for agents
agent_backend = StrandsAgentBackend()

# Use LangChain for models
model_backend = LangchainModelBackend()
```

## ⚠️ Important Notes

1. **Both backends are always installed** - No additional installation needed
2. **Explicit selection** - Backend is selected when creating backend instances
3. **No restart required** - You can switch backends by creating new instances
4. **Data compatibility** - Agent runs and configurations are compatible across backends
5. **No data loss** - Using different backends doesn't affect stored data
6. **Flexible architecture** - Different components can use different backends simultaneously

## 🐛 Troubleshooting

### Import errors
- Run `uv sync` to ensure all dependencies are installed
- Check Python version (3.10+)
- Verify no conflicting installations
- Ensure you're importing from the correct backend module

### Backend not available
- Verify the backend module exists: `from fivcplayground.backends.{backend_name} import ...`
- Check that all dependencies are installed for the backend you're using

### Performance issues
- Strands backend is optimized for agents
- LangChain backend is general-purpose
- Consider using Strands for agent-heavy workloads

---

**Last Updated**: 2025-11-25
**Version**: 0.1.0

