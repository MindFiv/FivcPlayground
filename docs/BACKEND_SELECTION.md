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

### Step 1: Edit Backend Configuration

Open `src/fivcplayground/__init__.py` and change the `__backend__` variable:

```python
# Current (Strands - Default)
__backend__ = "strands"

# Change to (LangChain)
__backend__ = "langchain"
```

### Step 2: Verify Dependencies

Both backends are installed by default. Verify with:

```bash
# Check Strands
python -c "import strands; print('Strands OK')"

# Check LangChain
python -c "import langchain_core; print('LangChain OK')"
```

### Step 3: Restart Application

```bash
# For CLI
uv run fivcplayground run Generic --query "test"

# For Web Interface
make serve
# or
uv run fivcplayground web
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

### Backend-Specific Code

The codebase uses conditional imports based on `__backend__`:

```python
from fivcplayground import __backend__

if __backend__ == "langchain":
    from .langchain import AgentRunnable
elif __backend__ == "strands":
    from .strands import AgentRunnable
```

### Affected Components

- **Agents** (`src/fivcplayground/agents/types/backends/`)
- **Models** (`src/fivcplayground/models/types/backends/`)
- **Tools** (`src/fivcplayground/tools/types/backends/`)

## ⚠️ Important Notes

1. **Both backends are always installed** - No additional installation needed
2. **Configuration is global** - Changing `__backend__` affects the entire application
3. **Restart required** - Changes take effect after application restart
4. **Data compatibility** - Agent runs and configurations are compatible across backends
5. **No data loss** - Switching backends doesn't affect stored data

## 🐛 Troubleshooting

### Backend not switching
- Verify you edited the correct file: `src/fivcplayground/__init__.py`
- Restart the application completely
- Check that `__backend__` is set correctly (no typos)

### Import errors
- Run `uv sync` to ensure all dependencies are installed
- Check Python version (3.10+)
- Verify no conflicting installations

### Performance issues
- Strands backend is optimized for agents
- LangChain backend is general-purpose
- Consider switching back to Strands if experiencing slowdowns

---

**Last Updated**: 2025-11-25
**Version**: 0.1.0

