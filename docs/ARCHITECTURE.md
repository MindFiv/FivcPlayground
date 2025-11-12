# Architecture Diagram: Persistent MCP Connections

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Streamlit Application                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ main()                                                       │  │
│  │                                                              │  │
│  │  1. _initialize_mcp_loader()  ← @st.cache_resource         │  │
│  │     ├─ loader = default_mcp_loader                          │  │
│  │     └─ loader.load()                                        │  │
│  │                                                              │  │
│  │  2. atexit.register(_cleanup_mcp_loader)                    │  │
│  │                                                              │  │
│  │  3. Build UI and run navigation                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      ToolsLoader Instance                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Attributes:                                                  │  │
│  │ • config: ToolsConfig                                        │  │
│  │ • tools_retriever: ToolsRetriever                            │  │
│  │ • tools_bundles: Dict[str, Set[str]]                         │  │
│  │ • client: MultiServerMCPClient ← PERSISTENT                 │  │
│  │ • sessions: Dict[str, Session] ← PERSISTENT                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ load_async():                                                │  │
│  │ 1. Load config from file                                     │  │
│  │ 2. Create MultiServerMCPClient                               │  │
│  │ 3. For each server:                                          │  │
│  │    ├─ session = await client.session().__aenter__()          │  │
│  │    ├─ self.sessions[name] = session  ← KEEP ALIVE           │  │
│  │    ├─ tools = await load_mcp_tools(session)                  │  │
│  │    └─ retriever.add_batch(tools)                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ cleanup_async():                                             │  │
│  │ 1. For each session in self.sessions:                        │  │
│  │    └─ await session.__aexit__(None, None, None)              │  │
│  │ 2. Clear self.sessions                                       │  │
│  │ 3. Clear self.client                                         │  │
│  │ 4. Remove all tools from retriever                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    MCP Client & Sessions                            │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ MultiServerMCPClient                                         │  │
│  │                                                              │  │
│  │ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  │  │
│  │ │ Session 1       │  │ Session 2       │  │ Session N   │  │  │
│  │ │ (server1)       │  │ (server2)       │  │ (serverN)   │  │  │
│  │ │                 │  │                 │  │             │  │  │
│  │ │ ✅ OPEN         │  │ ✅ OPEN         │  │ ✅ OPEN     │  │  │
│  │ │ (persistent)    │  │ (persistent)    │  │ (persistent)│  │  │
│  │ └─────────────────┘  └─────────────────┘  └─────────────┘  │  │
│  │         ↓                    ↓                    ↓          │  │
│  │    [Tools]              [Tools]              [Tools]        │  │
│  │                                                              │  │
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
│  │ Tool uses session from self.sessions[bundle_name]           │  │
│  │ ↓                                                            │  │
│  │ Session is OPEN ✅                                          │  │
│  │ ↓                                                            │  │
│  │ Tool executes successfully ✅                               │  │
│  │ ↓                                                            │  │
│  │ Result returned to agent                                    │  │
│  │                                                              │  │
│  │ ❌ NO ClosedResourceError                                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Session Lifecycle Timeline

```
Time ──────────────────────────────────────────────────────────────→

App Start
  │
  ├─ _initialize_mcp_loader()
  │  ├─ loader.load()
  │  │  ├─ Create MultiServerMCPClient
  │  │  ├─ Open Session 1 ──────────────────────────────────────┐
  │  │  ├─ Open Session 2 ──────────────────────────────────────┤
  │  │  └─ Open Session N ──────────────────────────────────────┤
  │  │                                                           │
  │  └─ atexit.register(_cleanup_mcp_loader)                    │
  │                                                              │
  ├─ Build UI                                                    │
  │                                                              │
  ├─ Agent invokes tools                                         │
  │  ├─ Tool 1 uses Session 1 ✅                                │
  │  ├─ Tool 2 uses Session 2 ✅                                │
  │  └─ Tool N uses Session N ✅                                │
  │                                                              │
  ├─ ... Application running ...                                │
  │                                                              │
  └─ App Shutdown                                                │
     │                                                           │
     ├─ atexit handler triggered                                │
     │  └─ _cleanup_mcp_loader()                                │
     │     └─ loader.cleanup()                                  │
     │        ├─ Close Session 1 ◄──────────────────────────────┤
     │        ├─ Close Session 2 ◄──────────────────────────────┤
     │        └─ Close Session N ◄──────────────────────────────┘
     │
     └─ All resources released ✅
```

## Data Flow: Tool Invocation

```
┌──────────────┐
│ Agent        │
│ (LangGraph)  │
└──────┬───────┘
       │ invoke_tool(tool_name, args)
       ↓
┌──────────────────────────────┐
│ ToolsRetriever               │
│ (Tool Registry)              │
└──────┬───────────────────────┘
       │ get_tool(tool_name)
       ↓
┌──────────────────────────────┐
│ Tool                         │
│ (LangChain Tool)             │
└──────┬───────────────────────┘
       │ call(args)
       ↓
┌──────────────────────────────┐
│ MCP Tool Wrapper             │
│ (langchain-mcp-adapters)     │
└──────┬───────────────────────┘
       │ call_tool(tool_name, args)
       ↓
┌──────────────────────────────┐
│ Session                      │
│ (from self.sessions)         │
│ ✅ OPEN & PERSISTENT         │
└──────┬───────────────────────┘
       │ send_request()
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

### Before (Broken)
```
Session created → Tools loaded → Session closed ❌
                                      ↓
                              Tool invocation fails
                              ClosedResourceError ❌
```

### After (Fixed)
```
Session created → Tools loaded → Session KEPT OPEN ✅
                                      ↓
                              Tool invocation succeeds ✅
                                      ↓
                              Session closed on shutdown ✅
```

