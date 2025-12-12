# Quick Start Guide: FivcPlayground with Persistent MCP Connections

**Last Updated**: 2025-10-30  
**Status**: ✅ Production Ready

---

## What's New

FivcPlayground now has:
- ✅ Persistent MCP connections (tools stay connected)
- ✅ Proper asyncio handling in Streamlit
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

### Start Streamlit
```bash
# Using the CLI (recommended)
uv run fivcplayground web

# Or using make
make serve

# Or directly with streamlit
streamlit run src/fivcplayground/app/__init__.py
```

### Expected Behavior
- ✅ App starts without errors
- ✅ MCP tools load successfully
- ✅ Chat interface is responsive
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
   - `create_tool_retriever(load_mcp_tools=True)` - Load MCP tools
   - `retrieve_tools(query)` - Semantic search for tools
   - `list_tools()` - List all available tools

2. **Streamlit Integration** - Lifecycle management
   - `create_tool_retriever()` - Initialize tool retriever
   - `nest_asyncio.apply()` - Asyncio patching
   - Automatic resource cleanup

3. **MCP Client** - Connection management
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

# Check logs
streamlit run src/fivcplayground/app/__init__.py --logger.level=debug
```

### Issue: Tools not loading

**Check**:
1. MCP servers are configured in configs/tools.yaml
2. MCP servers are running
3. Network connectivity

**Solution**:
```bash
# Test tool retriever
python -c "from fivcplayground.tools import create_tool_retriever; retriever = create_tool_retriever(load_mcp_tools=True); print(f'Loaded {len(retriever.list_tools())} tools')"

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
# Restart Streamlit app
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
2. Restart Streamlit app
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
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from fivcplayground.app import main
main()
"
```

---

## Performance Tips

1. **Reuse connections** - Sessions stay open (automatic)
2. **Batch operations** - Use tool bundles
3. **Monitor resources** - Check system memory
4. **Cache results** - Use Streamlit caching

---

## Common Tasks

### Create Tool Retriever with MCP Tools

```python
from fivcplayground.tools import create_tool_retriever

# Create a tool retriever with MCP tools loaded
retriever = create_tool_retriever(load_mcp_tools=True)

# List all tools (including bundles)
tools = retriever.list_tools()
for tool in tools:
    print(f"- {tool.name}: {tool.description}")

# Search for tools using semantic search
relevant_tools = retriever.retrieve_tools("calculate math")

# Get a specific tool by name
calculator = retriever.get_tool("calculator")
```

### Search for Tools

```python
from fivcplayground.tools import create_tool_retriever

# Create a tool retriever
retriever = create_tool_retriever(load_mcp_tools=True)

# Semantic search for relevant tools
query = "I need to perform a calculation"
relevant_tools = retriever.retrieve_tools(query)

print(f"Found {len(relevant_tools)} relevant tools:")
for tool in relevant_tools:
    print(f"  - {tool.name}")
```

---

## Documentation

For more detailed information, see:
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and MCP connections
- **[DESIGN.md](DESIGN.md)** - System design and components
- **[WEB_INTERFACE.md](WEB_INTERFACE.md)** - Web interface guide
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
- **Streamlit**: 1.49.1+
- **nest-asyncio**: 1.6.0+
- **langchain-mcp-adapters**: 0.1.11+

---

## Status

✅ **Production Ready**

All systems operational. Ready for deployment.

