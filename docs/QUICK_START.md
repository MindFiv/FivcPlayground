# Quick Start Guide: FivcPlayground with Persistent MCP Connections

**Last Updated**: 2025-10-30  
**Status**: ✅ Production Ready

---

## What's New

FivcPlayground now has:
- ✅ Persistent MCP connections (tools stay connected)
- ✅ Clean resource management
- ✅ No more connection errors

---

## Installation

### 1. Install Dependencies
```bash
# Navigate to the project directory
cd /path/to/fivcplayground

# Install dependencies using uv (recommended)
uv sync

# Or using make
make install
```

### 2. Verify Installation
```bash
uv run pytest tests/ -q
# Expected: 426+ tests passed
```

---

## Running the App

### Run an Agent
```bash
# Using the CLI (recommended)
uv run fivcplayground run Generic --query "What is machine learning?"

# Show available commands
uv run fivcplayground --help
```

### Expected Behavior
- ✅ Agent runs without errors
- ✅ MCP tools load successfully
- ✅ Tools can be invoked without errors

---

## Configuration

### MCP Configuration File

Create `mcp.yml` in the project root:

```yaml
servers:
  playwright:
    type: stdio
    command: python
    args:
      - -m
      - mcp.server.playwright
    env:
      PYTHONPATH: /path/to/mcp/servers
```

### Environment Variables

```bash
# Optional: specify custom MCP config file
export MCP_FILE=/path/to/mcp.yml
```

---

## Architecture Overview

### Session Lifecycle

```
App Start
  ↓
Initialize MCP Loader (cached)
  ├─ Create MultiServerMCPClient
  ├─ Open sessions (keep alive) ✅
  ├─ Load tools
  └─ Register cleanup handler
  ↓
Agent Invokes Tools
  ├─ Tool uses open session ✅
  └─ No errors ✅
  ↓
App Shutdown
  ├─ Close all sessions
  ├─ Clear resources
  └─ Clean exit ✅
```

### Key Components

1. **ToolRetriever** - Manages tool retrieval and MCP connections
   - `create_tool_retriever_async()` - Create tool retriever
   - `retrieve_tools_async(query)` - Semantic search for tools
   - `list_tools_async()` - List all available tools

2. **MCP Client** - Connection management
   - Persistent connections
   - Session reuse
   - Error handling

---

## Troubleshooting

### Issue: App won't start

**Check**:
1. MCP configuration file exists
2. MCP servers are running
3. No port conflicts

**Solution**:
```bash
# Check MCP config
cat mcp.yml

# Verify MCP servers
ps aux | grep mcp

# Run an agent with verbose logging
uv run fivcplayground run Generic --query "test" --verbose
```

### Issue: Tools not loading

**Check**:
1. MCP servers are configured in configs/tools.yaml
2. MCP servers are running
3. Network connectivity

**Solution**:
```bash
# Test tool retriever
python -c "
import asyncio
from fivcplayground.tools import create_tool_retriever_async
from fivcplayground.backends.strands.tools import StrandsToolBackend

async def test():
    retriever = await create_tool_retriever_async(tool_backend=StrandsToolBackend())
    tools = await retriever.list_tools_async()
    print(f'Loaded {len(tools)} tools')

asyncio.run(test())
"

# Check logs for errors
# Look for "Error loading tools from" messages
```

### Issue: Slow performance

**Check**:
1. MCP servers are responsive
2. Network latency
3. System resources

**Solution**:
```bash
# Monitor system resources
top

# Check network latency
ping <mcp-server-host>

# Restart MCP servers
# Re-run the agent
```

---

## Development

### Running Tests

```bash
# All tests
uv run pytest tests/ -q

# Specific test file
uv run pytest tests/test_tools_loader.py -xvs

# With coverage
uv run pytest tests/ --cov=src/fivcplayground
```

### Adding New Tools

1. Configure MCP server in `configs/tools.yaml`
2. Re-run the agent
3. Tools automatically load

Example tool configuration:
```yaml
my_server:
  description: "My MCP server"
  transport: "stdio"
  command: "python"
  args: ["server.py"]
```

### Debugging

```bash
# Enable debug logging
export PYTHONPATH=/path/to/project
uv run fivcplayground run Generic --query "test" --verbose
```

---

## Performance Tips

1. **Reuse connections** - Sessions stay open (automatic)
2. **Batch operations** - Use tool bundles
3. **Monitor resources** - Check system memory

---

## Common Tasks

### Create Tool Retriever

```python
import asyncio
from fivcplayground.tools import create_tool_retriever_async
from fivcplayground.backends.strands.tools import StrandsToolBackend

async def main():
    # Create a tool retriever with explicit backend selection
    retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend()
    )

    # List all tools (including bundles)
    tools = await retriever.list_tools_async()
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")

    # Search for tools using semantic search
    relevant_tools = await retriever.retrieve_tools_async("calculate math")

    # Get a specific tool by name
    calculator = await retriever.get_tool_async("calculator")

asyncio.run(main())
```

### Search for Tools

```python
import asyncio
from fivcplayground.tools import create_tool_retriever_async
from fivcplayground.backends.strands.tools import StrandsToolBackend

async def main():
    # Create a tool retriever with explicit backend selection
    retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend()
    )

    # Semantic search for relevant tools
    query = "I need to perform a calculation"
    relevant_tools = await retriever.retrieve_tools_async(query)

    print(f"Found {len(relevant_tools)} relevant tools:")
    for tool in relevant_tools:
        print(f"  - {tool.name}")

asyncio.run(main())
```

---

## Documentation

For more detailed information, see:
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and MCP connections
- **[DESIGN.md](DESIGN.md)** - System design and components
- **[DEPENDENCIES.md](DEPENDENCIES.md)** - Dependency management
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - MCP implementation details

---

## Support

### Getting Help

1. Check documentation files
2. Review test cases for examples
3. Check application logs
4. Review error messages

### Reporting Issues

Include:
1. Error message and stack trace
2. Steps to reproduce
3. System information
4. MCP configuration

---

## Version Info

- **FivcPlayground**: 0.1.0
- **Python**: 3.10+
- **nest-asyncio**: 1.6.0+
- **langchain-mcp-adapters**: 0.1.11+

---

## Status

✅ **Production Ready**

All systems operational. Ready for deployment.

