# FivcPlayground TOOLS KNOWLEDGE BASE

**Generated:** 2026-01-26
**Commit:** N/A
**Branch:** N/A

## OVERVIEW
Tool management system with builtin tools and MCP (Model Context Protocol) integration for dynamic tool retrieval and semantic search.

## STRUCTURE
```
src/fivcplayground/tools/
├── types/               # Tool type definitions and interfaces
│   ├── base.py         # Tool, ToolBundle, ToolBackend abstract classes
│   ├── bundles.py      # FunctionToolBundle implementation
│   ├── retrievers.py   # ToolRetriever for semantic search
│   └── repositories/   # Tool configuration storage
├── calculator.py       # Mathematical operations tool
├── clock.py           # Time and date information tool
├── filesystem.py      # File operations (read, write, search)
└── shell.py           # System command execution tool
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Tool factory | `tools/__init__.py` | `create_builtin_tools_async()` creates all builtin tools |
| Tool retrieval | `tools/types/retrievers.py` | Semantic search with embedding integration |
| Tool bundles | `tools/types/bundles.py` | FunctionToolBundle groups related tools |
| Tool backend | `tools/types/base.py` | Abstract ToolBackend interface |
| Builtin tools | `tools/*.py` | calculator, clock, filesystem, shell tools |
| Tool config | `tools/types/base.py` | ToolConfig model for MCP integration |

## CONVENTIONS

### Tool Architecture
- All tools are async-first with proper error handling
- Tools return strings, never raise exceptions (error messages prefixed with "Error:")
- Tool functions use comprehensive docstrings with examples
- ToolBackend abstracts backend-specific tool creation (Strands/LangChain)

### Tool Bundles
- FunctionToolBundle groups related tools (auxiliary, filesystem)
- ToolBundleContext manages async tool lifecycle
- MCP tools created via ToolBackend.create_tool_bundle()

### Tool Retrieval
- ToolRetriever provides semantic search using embeddings
- Tools indexed by name and description for intelligent retrieval
- Configurable similarity thresholds and result limits

## ANTI-PATTERNS (THIS PROJECT)

### Forbidden Patterns
- Don't create tools without using ToolBackend.create_tool()
- Don't bypass ToolRetriever for tool discovery
- Don't raise exceptions from tool functions (return error strings)
- Don't use sync methods in tool implementations

### Tool Implementation
- Always include comprehensive docstrings with examples
- Always handle errors gracefully with descriptive error messages
- Always validate inputs before processing
- Always return string results (never complex objects)

### MCP Integration
- Don't manually instantiate MCP tools (use ToolBackend)
- Don't ignore ToolConfig transport protocols (stdio, sse, streamable_http)
- Don't bypass ToolConfigRepository for configuration management