# Architecture Diagram: Tool Retrieval with MCP Support

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Streamlit Application                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ main()                                                       │  │
│  │                                                              │  │
│  │  1. Create repositories                                      │  │
│  │     ├─ FileEmbeddingConfigRepository                         │  │
│  │     ├─ FileToolConfigRepository                              │  │
│  │     └─ FileModelConfigRepository                             │  │
│  │                                                              │  │
│  │  2. Create tool retriever                                    │  │
│  │     └─ create_tool_retriever_async()                         │  │
│  │                                                              │  │
│  │  3. Build UI and run navigation                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      ToolRetriever Instance                         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Attributes:                                                  │  │
│  │ • tools: Dict[str, Tool]  ← Built-in tools                  │  │
│  │ • tool_config_repository: ToolConfigRepository               │  │
│  │ • tool_indices: EmbeddingDB  ← Semantic search               │  │
│  │ • max_num: int  ← Top-K results                              │  │
│  │ • min_score: float  ← Relevance threshold                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Methods:                                                     │  │
│  │ • list_tools() → List[Tool]                                  │  │
│  │   Returns all tools (built-in + MCP bundles)                 │  │
│  │                                                              │  │
│  │ • get_tool(name) → Tool | None                               │  │
│  │   Get specific tool by name                                  │  │
│  │                                                              │  │
│  │ • retrieve_tools(query) → List[Tool]                         │  │
│  │   Semantic search for relevant tools                         │  │
│  │                                                              │  │
│  │ • index_tools()                                              │  │
│  │   Index all tools for semantic search                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Tool Loading (via create_tool_retriever):                    │  │
│  │ 1. Load built-in tools (clock, calculator)                   │  │
│  │ 2. Load tool configs from repository                         │  │
│  │    ├─ Create ToolBundle for each config                      │  │
│  │    └─ Add bundles to tool list                               │  │
│  │ 3. Create ToolRetriever with all tools                       │  │
│  │ 4. Index tools for semantic search                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent Execution                                │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Agent invokes tool                                           │  │
│  │ ↓                                                            │  │
│  │ Tool is retrieved from ToolRetriever                         │  │
│  │ ↓                                                            │  │
│  │ If tool is ToolBundle:                                       │  │
│  │   ├─ Load MCP tools asynchronously                           │  │
│  │   └─ Execute tool with loaded session                        │  │
│  │ ↓                                                            │  │
│  │ Tool executes successfully ✅                               │  │
│  │ ↓                                                            │  │
│  │ Result returned to agent                                    │  │
│  │                                                              │  │
│  │ ✅ Clean resource management                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Tool Retriever Initialization Timeline

```
Time ──────────────────────────────────────────────────────────────→

App Start
  │
  ├─ Create repositories
  │  ├─ FileEmbeddingConfigRepository
  │  ├─ FileToolConfigRepository
  │  └─ FileModelConfigRepository
  │
  ├─ create_tool_retriever_async()
  │  ├─ Load built-in tools (clock, calculator)
  │  ├─ Load tool configs from repository
  │  ├─ Create ToolBundle for each config
  │  ├─ Create ToolRetriever with all tools
  │  └─ Index tools for semantic search
  │
  ├─ Build UI
  │
  ├─ Agent invokes tools
  │  ├─ retrieve_tools(query) - semantic search
  │  ├─ get_tool(name) - get specific tool
  │  └─ Tool executes (ToolBundle loads MCP tools on demand)
  │
  ├─ ... Application running ...
  │
  └─ App Shutdown
     │
     └─ All resources released ✅
```

## Data Flow: Tool Invocation

```
┌──────────────┐
│ Agent        │
│ (Strands)    │
└──────┬───────┘
       │ invoke_tool(tool_name, args)
       ↓
┌──────────────────────────────┐
│ ToolRetriever               │
│ (Tool Registry)              │
└──────┬───────────────────────┘
       │ get_tool(tool_name)
       ↓
┌──────────────────────────────┐
│ Tool or ToolBundle           │
│ (Built-in or MCP)            │
└──────┬───────────────────────┘
       │ call(args) or load_async()
       ↓
┌──────────────────────────────┐
│ If ToolBundle:               │
│ Load MCP tools asynchronously│
│ (on-demand loading)          │
└──────┬───────────────────────┘
       │ execute_tool(args)
       ↓
┌──────────────────────────────┐
│ MCP Tool Wrapper             │
│ (langchain-mcp-adapters)     │
└──────┬───────────────────────┘
       │ call_tool(tool_name, args)
       ↓
┌──────────────────────────────┐
│ MCP Server                   │
│ (e.g., Playwright, etc.)     │
└──────┬───────────────────────┘
       │ execute_tool()
       ↓
┌──────────────────────────────┐
│ Result                       │
└──────┬───────────────────────┘
       │ return result
       ↓
┌──────────────────────────────┐
│ Agent                        │
│ (receives result)            │
└──────────────────────────────┘
```

## Key Improvements

### Architecture Simplification
```
Before (with ToolLoader):
  create_tool_retriever() → create_tool_loader() → loader.load()
  (3 steps, deprecated synchronous methods)

After (without ToolLoader):
  await create_tool_retriever_async()
  (1 step, cleaner async API)
```

### Benefits
- **Simpler API**: Single factory call instead of multiple steps
- **Immutable Design**: Tools loaded at initialization, not added later
- **On-Demand Loading**: ToolBundle loads MCP tools when needed
- **Better Resource Management**: Automatic cleanup with async context managers
- **Cleaner Code**: No deprecated methods, less maintenance burden

