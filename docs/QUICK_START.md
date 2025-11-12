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
cd /Users/charlie/Works/FivcPlayground
uv sync
```

### 2. Verify Installation
```bash
uv run pytest tests/ -q
# Expected: 510 passed
```

---

## Running the App

### Start Streamlit
```bash
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

1. **ToolsLoader** - Manages MCP connections
   - `load()` - Synchronous loading
   - `load_async()` - Asynchronous loading
   - `cleanup()` - Resource cleanup

2. **Streamlit Integration** - Lifecycle management
   - `_initialize_mcp_loader()` - Cached initialization
   - `_cleanup_mcp_loader()` - Cleanup on shutdown
   - `nest_asyncio.apply()` - Asyncio patching

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
1. MCP servers are configured
2. MCP servers are running
3. Network connectivity

**Solution**:
```bash
# Test MCP connection
python -c "from fivcplayground.tools import default_loader; default_loader.load()"

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

1. Configure MCP server in `mcp.yml`
2. Restart Streamlit app
3. Tools automatically load

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

### Reload MCP Configuration

```python
from fivcplayground.app.utils import default_mcp_loader

# Reload configuration
loader = default_mcp_loader
loader.cleanup()
loader.load()
```

### Check Loaded Tools

```python
from fivcplayground.tools import default_retriever

# List all tools (including bundles)
tools = default_retriever.get_all()
for tool in tools:
    print(f"- {tool.name}: {tool.description}")

# Search for tools (returns bundles as-is)
relevant_tools = default_retriever.retrieve("calculate math")

# Search and expand bundles into individual tools
expanded_tools = default_retriever.retrieve("calculate math", expand=True)
```

### Monitor Connections

```python
from fivcplayground.app.utils import default_mcp_loader

loader = default_mcp_loader
print(f"Client: {loader.client}")
print(f"Sessions: {list(loader.sessions.keys())}")
print(f"Tools: {loader.tools_bundles}")
```

---

## Documentation

- **PERSISTENT_MCP_CONNECTIONS.md** - Architecture details
- **NEST_ASYNCIO_FIX.md** - Asyncio fix explanation
- **ASYNCIO_ISSUE_RESOLUTION.md** - Problem analysis
- **ARCHITECTURE_DIAGRAM.md** - Visual diagrams

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

