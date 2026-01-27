# FivcPlayground KNOWLEDGE BASE

**Generated:** 2026-01-26
**Commit:** N/A
**Branch:** N/A

## OVERVIEW
Pluggable backend implementations for Strands (default) and LangChain with unified interfaces.

## STRUCTURE
```
backends/
├── strands/         # Strands backend (default)
│   ├── agents.py     # Agent implementation with message conversion
│   ├── tools.py      # Tool integration and MCP client
│   ├── models.py     # Model backend interface
│   └── tasks.py      # Task execution backend
├── langchain/        # LangChain backend (alternative)
│   ├── agents.py     # Agent implementation with LangChain mapping
│   ├── tools.py      # Tool integration with langchain-mcp-adapters
│   ├── models.py     # Model backend interface
│   └── tasks.py      # Task execution backend
├── chroma/           # ChromaDB embedding backend
│   ├── embeddings.py # Vector database operations
│   └── splitters.py  # Document splitting utilities
└── faiss.py          # FAISS vector backend (not implemented)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Backend selection | `backends/__init__.py` | Factory functions for backend instantiation |
| Message conversion | `strands/agents.py`, `langchain/agents.py` | Converts between internal and backend-specific formats |
| Tool integration | `*/tools.py` | MCP client integration differs per backend |
| Model abstraction | `*/models.py` | Unified model interface across backends |
| Vector operations | `chroma/embeddings.py` | Embedding storage and retrieval |

## CONVENTIONS

### Backend Interface Pattern
- All backends implement same abstract interfaces from parent domains
- Backend classes follow `{Backend}{Domain}Backend` naming convention
- Message conversion handled internally, transparent to callers
- Async-first design with sync wrappers where needed

### Message Conversion
- Strands: Uses `Message`, `ContentBlock`, `ToolUse`, `ToolResult` types
- LangChain: Uses `HumanMessage`, `AIMessage`, `ToolMessage` from langchain_core
- Conversion preserves metadata and tool call structure
- Error handling maintains backend-agnostic exceptions

### Tool Integration
- Strands: Native MCP client with `strands.tools.mcp.MCPClient`
- LangChain: Uses `langchain_mcp_adapters` for MCP integration
- Both support stdio, SSE, and HTTP connection types
- Tool loading unified through common interfaces

## ANTI-PATTERNS (THIS PROJECT)

### Forbidden Patterns
- Don't mix backend-specific types in domain layer
- Don't bypass backend interfaces for direct library calls
- Don't implement backend logic without extending base classes
- Don't create backend-specific configuration in core domains

### Backend Anti-Patterns
- Don't hardcode backend selection in application code
- Don't expose backend-internal types to callers
- Don't implement message conversion manually (use adapters)
- Don't create duplicate tool integrations across backends