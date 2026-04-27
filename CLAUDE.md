# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start Commands

### Setup & Installation
```bash
# Install all dependencies including dev tools
make install

# Install runtime dependencies only
make install-min

# Show available make commands
make help
```

### Development
```bash
# Run code linting
make lint

# Format code with ruff
make format

# Run test suite
make test

# Run single test file
uv run pytest tests/path/to/test_file.py -v

# Run single test function
uv run pytest tests/path/to/test_file.py::test_function_name -v

# Clean temporary files and caches
make clean
```

### Running the Application
```bash
# Start web interface (Streamlit)
make serve

# Development web mode with auto-reload
make serve-dev

# Run CLI agent
uv run fivcplayground run Generic --query "Your question here"

# Set up initial configuration
uv run fivcplayground setup

# Show system information
uv run fivcplayground info

# Clean up temporary files
uv run fivcplayground clean
```

## High-Level Architecture

### System Overview

FivcPlayground is an intelligent multi-agent system with **pluggable backends**. It features:
- **Agent-based execution** - Specialized agents for different task types
- **Dynamic tool retrieval** - Semantic search-based tool selection
- **Multiple backends** - Strands (primary), Google ADK, and extensible architecture
- **Web UI** - Streamlit-based modern interface
- **Streaming support** - Real-time response streaming and event callbacks

### Core Architecture Layers

```
┌─────────────────────────────────────────────────┐
│   CLI / Web Interface (labs module)            │
│   - Command-line interface (cli.py)             │
│   - Streamlit web UI (labs/)                   │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│   Factory & Coordination Layer                  │
│   - create_agent_async()                        │
│   - create_tool_retriever_async()               │
│   - create_model_async()                        │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│   Backend Layer                                 │
│   - StrandsAgentBackend (primary)               │
│   - StrandsModelBackend                         │
│   - StrandsToolBackend                          │
│   - GoogleADKAgentBackend (alternative)         │
│   - GoogleADKModelBackend                       │
│   - GoogleADKToolBackend                        │
│   - ChromaEmbeddingBackend                      │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│   Repository Layer (Data Access)                │
│   - AgentConfigRepository                       │
│   - AgentRunRepository                          │
│   - ModelConfigRepository                       │
│   - ToolConfigRepository                        │
│   - EmbeddingConfigRepository                   │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────┐
│   Storage                                       │
│   - ~/.fivcplayground/ (YAML configs & runs)    │
│   - Chroma embeddings database                  │
└─────────────────────────────────────────────────┘
```

### Key Components & Responsibilities

#### 1. Agents System (`src/fivcplayground/agents/`)
- **AgentConfig** - Configuration for an agent (model_id, tools, system prompt)
- **Agent Types**:
  - `default` - Standard task execution
  - `companion` - Casual conversation
  - `tooling` - Tool selection specialist
  - `consultant` - Task assessment
  - `planner` - Execution planning
  - `researcher` - Pattern analysis
  - `engineer` - Tool development
  - `evaluator` - Performance assessment
- **Execution Flow**: Loads config → creates model → injects tools → streams execution
- **Key Types**: `AgentRun` (execution record), `AgentRunToolCall` (tool invocation), `AgentRunStatus` (state)
- **Tool Configuration and Merging**:
  - Agents support two sources for tool configuration:
    1. **Agent Config** (`agent_config.tool_ids`) - Defined in YAML config
    2. **Runtime Parameter** (`run_async(tool_ids=[...])`) - Passed at execution time
  - **Merging Logic** (v0.1.19+):
    - Both sources are **merged using set union**
    - Duplicates are automatically eliminated
    - Order is not guaranteed (set-based deduplication)
    - Example:
      ```python
      # Agent config: tool_ids=["calculator", "clock"]
      # Runtime call: run_async(tool_ids=["clock", "filesystem"])
      # Result: ["calculator", "clock", "filesystem"] (deduplicated)
      ```
  - **Implementation**: Located in `StrandsAgentRunnable.run_async()`
  - **Backward Compatibility Note**:
    - Prior to v0.1.19: Runtime `tool_ids` overrode config `tool_ids`
    - From v0.1.19: Runtime `tool_ids` extends config `tool_ids`
- **Skill ID Configuration and Merging** (`skill_ids`):
  - `AgentConfig.skill_ids` is merged with the runtime `skill_ids` parameter via set union (same behavior as `tool_ids`)
  - When the merged set is empty, `None` is passed to `to_tool()` to preserve "show all skills" semantics
  - Example: config `skill_ids=["data-analyzer"]` + runtime `skill_ids=["researcher"]` → `["data-analyzer", "researcher"]`
- **Structured Output Support**:
  - Agents support type-safe, structured responses using Pydantic models
  - Two configuration methods:
    1. **JSON Schema in Agent Config** - Define `response_format` in YAML
    2. **Runtime Pydantic Model** - Pass `response_model` parameter to `run_async()`
  - **Storage**: Structured output stored in two forms:
    - Pydantic instance returned from `run_async()` for immediate use
    - JSON dict in `agent_run.reply.structured` field for persistence
  - **Example**:
    ```python
    from pydantic import BaseModel, EmailStr
    from fivcplayground.agents import create_agent_async

    class ContactInfo(BaseModel):
        name: str
        email: EmailStr

    agent = await create_agent_async("data_extractor")
    result = await agent.run_async(
        query="Extract contact: John Doe (john@example.com)",
        response_model=ContactInfo
    )
    # result is a ContactInfo instance
    print(result.name)   # "John Doe"
    print(result.email)  # "john@example.com"
    ```
  - **Retrieval from Storage**:
    ```python
    # Access structured output from saved runs
    agent_run = await repo.get_agent_run_async(session_id, run_id)
    if agent_run.reply and agent_run.reply.structured:
        data = agent_run.reply.structured  # dict[str, Any]
        print(data["name"], data["email"])
    ```
  - **Backend Support**: Strands backend fully supports structured output

#### 2. Tools System (`src/fivcplayground/tools/`)
- **Built-in Tools**: clock, calculator, filesystem, shell
- **Tool Retrieval**:
  - Semantic search via embeddings to find relevant tools for a query
  - Configurable similarity threshold and max results
  - Tools indexed by description in Chroma vector database
- **Tool Types**:
  - `StrandsTool` - Function-based tools
  - `FunctionToolBundle` - Multiple related functions
  - `StrandsToolBundle` - MCP protocol tools (Playwright, Chrome DevTools, etc.)

#### 3. Models System (`src/fivcplayground/models/`)
- **Model Abstraction**: Supports OpenAI and Ollama providers
- **Model Config**: Temperature, max_tokens, base_url, API keys
- **Model Selection**: Specialist models for different agent types (chat, reasoning, default)
- **Backend Adapters**: StrandsModel wraps Strands framework

#### 4. Embeddings System (`src/fivcplayground/embeddings/`)
- **EmbeddingDB**: Chroma-based vector search for semantic similarity
- **Usage**: Tool description indexing for dynamic tool retrieval
- **Configuration**: EmbeddingConfig specifies database path and collection names

#### 5. Web Interface (`src/fivcplayground/labs/`)
- **Architecture**:
  - ViewNavigation (custom sidebar navigation replacing st.navigation)
  - ChatView (per-conversation UI)
  - ChatManager (conversation state and agent execution coordination)
  - Components (ChatMessage rendering with thinking extraction, tool visualization)
- **Key Features**:
  - Real-time streaming with delta message handling
  - Thinking extraction from XML tags (`<think>...</think>`)
  - Tool call visualization with status and timing
  - Multi-chat session support
- **State Management**: Session-based with run.yml for view persistence

#### 6. Backends (`src/fivcplayground/backends/`)

**Strands Backend** (primary):
  - StrandsAgentRunnable - Agent execution wrapper
  - StrandsModelBackend - Model factory
  - StrandsToolBackend - Tool factory
  - Supports streaming via `stream_async()`

**Google ADK Backend** (alternative):
  - GoogleADKAgentRunnable - Agent execution wrapper
  - GoogleADKModelBackend - Model factory
  - GoogleADKToolBackend - Tool factory
  - Supports Gemini, Claude, and other models
  - Same API as Strands backend for easy switching
  - Install: `pip install google-adk`
  - See `examples/google_adk_backend_example.py` for usage

**Chroma Backend**:
  - Embedding storage and retrieval
  - Multi-space support for isolation

### Backend Selection & Switching

Both Strands and Google ADK backends implement the same abstract interfaces (`AgentBackend`, `ToolBackend`, `ModelBackend`). Switch backends by importing different backend classes:

```python
# Strands backend (current default)
from fivcplayground.backends.strands import (
    StrandsAgentBackend, StrandsModelBackend, StrandsToolBackend
)

# Google ADK backend (alternative)
from fivcplayground.backends.google_adk import (
    GoogleADKAgentBackend, GoogleADKModelBackend, GoogleADKToolBackend
)

# Instantiate chosen backend
agent_backend = GoogleADKAgentBackend()  # or StrandsAgentBackend()
model_backend = GoogleADKModelBackend()  # or StrandsModelBackend()
tool_backend = GoogleADKToolBackend()    # or StrandsToolBackend()

# Rest of code works identically with either backend
agent = await agent_backend.create_agent_async(
    model_backend=model_backend,
    model_config_repository=model_repo,
    agent_config=agent_config,
)
```

### Design Patterns Used

| Pattern | Usage | Key Classes |
|---------|-------|------------|
| **Factory** | Create agents, models, tools, retrievers | `create_agent_async()`, `create_model_async()` |
| **Repository** | Data access abstraction | `FileAgentConfigRepository`, `FileAgentRunRepository` |
| **Abstract Factory** | Pluggable backends | `AgentBackend`, `ToolBackend`, `ModelBackend` |
| **Adapter** | Backend adapters | `StrandsAgentRunnable` |
| **Decorator** | Agent composition | `BoundedAgentRunnable`, `ParameterizedAgentRunnable` |
| **Semantic Search** | Tool retrieval | `ToolRetriever` + `EmbeddingDB` |
| **Event-Driven** | Streaming execution | `AgentRunEvent` callbacks (START, STREAM, TOOL, UPDATE) |

### Configuration-Driven Architecture

Configuration files in `~/.fivcplayground/configs/` (YAML format):
- **agents.yaml** - Agent definitions with model references, tools, system prompts
- **models.yaml** - LLM model configurations (provider, API keys, parameters)
- **tools.yaml** - Tool bundle configurations (MCP servers)
- **embeddings.yaml** - Embedding database configuration (Chroma settings)

### Agent Execution Flow

```
1. Load AgentConfig from repository
2. Create LLM model via ModelBackend
3. Retrieve relevant tools via ToolRetriever
   └─ Semantic search by description
4. Execute agent via AgentBackend
   ├─ Initialize with model + tools + system prompt
   ├─ Stream execution events
   ├─ Track tool calls in AgentRun
   └─ Save conversation to AgentRunRepository
5. Update UI via event callbacks (START, STREAM, TOOL, UPDATE, FINISH)
```

### Tool Retrieval Flow

```
1. Query comes in: "Find information about X"
2. ToolRetriever searches embeddings by description
3. Filter by similarity_score >= min_sim threshold (default 0.3)
4. Return top_k results (default 5)
5. Tools injected into agent prompt
```

## Key Architectural Decisions

1. **Async-First Design** - All core functions use `*_async()` suffix for streaming and concurrency
2. **Pluggable Backends** - Multiple backend implementations (Strands, Google ADK, extensible)
3. **Semantic Tool Discovery** - Tools selected dynamically via embeddings, not just by name
4. **Configuration-Driven** - Agents, models, tools defined in YAML config files
5. **Event-Driven Streaming** - Real-time UI updates via event callbacks (streaming, tool calls, state)
6. **Repository Pattern** - Storage implementation agnostic (file-based by default)
7. **Modular Tool System** - Built-in tools + configurable MCP tool bundles
8. **Tool ID Union Merging** - Runtime and config tool_ids are merged (union), not overridden, allowing agents to have base tools while accepting additional tools at runtime
9. **Backend Abstraction** - Common interfaces (AgentBackend, ToolBackend, ModelBackend) enable backend switching without code changes

## Important Constraints

- **Single-Process Only**: File-based repositories are not suitable for multi-server deployments
- **Conversation Memory**: Hardcoded sliding window of 20 messages in `StrandsAgentRunnable`
- **Tool Execution Context**: MCP protocol tools require external process management
- **Streamlit Limitations**: Uses `nest_asyncio` to handle nested event loops in web UI

## Module Organization

- **`src/fivcplayground/agents/`** - Agent configuration, runtime, and types
- **`src/fivcplayground/tools/`** - Tool management, retrieval, and creation
- **`src/fivcplayground/models/`** - LLM model factories and provider abstractions
- **`src/fivcplayground/backends/`** - Backend implementations (Strands, LangChain, Chroma)
- **`src/fivcplayground/embeddings/`** - Vector database for semantic search
- **`src/fivcplayground/labs/`** - Streamlit web interface and components
- **`src/fivcplayground/cli.py`** - Command-line interface entry point
- **`src/fivcplayground/schemas.py`** - Pydantic data models
- **`src/fivcplayground/settings.py`** - Configuration and environment management
- **`tests/`** - Test suite with pytest markers for async tests

## Testing

Tests use pytest with async support:
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/agents/test_agent_config.py -v

# Run tests matching pattern
uv run pytest -k "test_create" -v

# Run with coverage
uv run pytest --cov=src/fivcplayground

# Skip asyncio tests (for faster execution)
uv run pytest -m "not asyncio"
```

Async tests are marked with `@pytest.mark.asyncio` decorator.

## Dependencies & Backend Selection

- **Runtime**: Strands, Typer, Rich, Pydantic, Streamlit, python-dotenv
- **Optional**: Chroma embeddings
- **Dev**: pytest, pytest-asyncio, ruff

Use `make install` to install everything.

## Skills & Dynamic Tool Loading

Skills enable agents to load specialized tools dynamically at runtime based on the skill being executed. This pattern allows agents to request relevant tools only when needed.

### Skill Configuration

Skills are defined in `~/.fivcplayground/configs/skills.yaml`:
```yaml
skills:
  data-analyzer:
    description: "Analyzes data with statistical tools"
    instructions: "Use calculator and clock to analyze time series"
    tool_ids: ["calculator", "clock"]
    resources:
      timeout: "300"
      memory_limit: "512MB"
```

### Dynamic Tool Loading with Callbacks

The skill retrieval system uses a callback pattern for dynamic tool loading:

1. **Callback Type**: `LoadCallback = Callable[[SkillConfig], None] | Callable[[SkillConfig], Awaitable[None]]`

2. **Strands Backend Pattern**:
```python
async def _extend_tools(skill: SkillConfig):
    """Callback to dynamically load skill tools."""
    for tool_id in skill.tool_ids or []:
        for tool in await agent_tool_span.register_tool_async(tool_id):
            agent.tool_registry.register_dynamic_tool(tool)

# Register skill tool with callback
agent.tool_registry.register_tool(
    skill_retriever.to_tool(load_callback=_extend_tools)
)
```

### Skill ID Filtering

The `to_tool()` method supports an optional `skill_ids` parameter to filter which skills are available:

```python
# Only make specific skills available to an agent
skill_tool = skill_retriever.to_tool(
    skill_ids=["data-analyzer", "researcher"],
    load_callback=_extend_tools,
)
```

**Filtering Behavior**:
- `skill_ids=None` (default) — All skills are available
- `skill_ids=[]` — No skills are available (empty list)
- `skill_ids=["id1", "id2"]` — Only specified skills are available in `skill_list()` and `skill_load()`
- Non-existent skill IDs are silently filtered out
- When `AgentConfig.skill_ids` is set, it is merged with the runtime `skill_ids` parameter via set union (same behavior as `tool_ids`). When the merged set is empty, `None` is passed to preserve "all skills" semantics.

**Use Cases**:
- Restrict agent capabilities by exposing only relevant skills
- Multi-tenant scenarios where different agents have different skill access
- Preventing unnecessary tool loading for specialized agents

### Runtime Tool Registration

The `AgentRunToolSpan.register_tool_async()` method handles dynamic tool registration:

- **Registers individual tools** or expands `ToolBundle` instances
- **Handles deduplication** across multiple registrations
- **Returns expanded tools** (for bundles, returns individual tools)
- **Accepts Tool objects or tool_id strings** (when `tool_retriever` is available)

### Implementation Details

- Tools are registered in `_tool_loaded_expanded` dict for deduplication
- ToolBundles are set up and stored in `_tool_contexts` for cleanup
- Context manager exit automatically cleans up all registered tools and contexts
- Strands backend supports the callback pattern

### Common Development Tasks

### Adding a New Tool
1. Define tool configuration in `~/.fivcplayground/configs/tools.yaml`
2. Or use `create_tool()` / `create_tool_bundle()` in code
3. ToolRetriever automatically indexes new tools
4. Tools selected dynamically by semantic search

### Adding a New Agent Type
1. Add agent configuration to `~/.fivcplayground/configs/agents.yaml`
2. Reference model_id and tools
3. Use `fivcplayground run <AgentName>` to execute
4. Custom system prompt in agent config

### Adding a New Skill
1. Define skill configuration in `~/.fivcplayground/configs/skills.yaml`
2. Specify `id`, `description`, `instructions`, and `tool_ids` (array of tool IDs)
3. Optional: add `resources` dictionary for resource constraints/metadata
4. SkillRetriever automatically indexes new skills for semantic search
5. When agent loads a skill, the callback dynamically registers specified tools:
   - Callback invoked with SkillConfig when skill is executed
   - Registers each tool_id via `AgentRunToolSpan.register_tool_async()`
   - Tools become available to agent for rest of execution
   - Deduplication prevents duplicate tool registration across multiple skills

Example:
```yaml
data-analyzer:
  description: "Analyzes data with statistical tools"
  instructions: "Use calculator and file tools to analyze data"
  tool_ids: ["calculator", "filesystem"]
  resources:
    timeout: "300"
```

### Debugging Agent Execution
- Check `~/.fivcplayground/runs/` for execution history
- Agent runs stored hierarchically by session and agent type
- Each run includes query, response, tool calls, and status
- Event callbacks in ChatManager can add custom logging

## Documentation

Comprehensive docs in `docs/` directory:
- **DESIGN.md** - System architecture deep dive
- **WEB_INTERFACE.md** - Streamlit UI development guide
- **DEPENDENCIES.md** - Installation and dependency management
- **ARCHITECTURE_PATTERNS.md** - Design patterns and best practices
