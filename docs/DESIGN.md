# 🚀 FivcPlayground System Design

> *An intelligent agent ecosystem built on Strands for autonomous tool generation, task assessment, and dynamic agent orchestration*

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [🏗️ Architecture](#️-architecture)
- [🤖 Agent System](#-agent-system)
- [🧰 Tool Management](#-tool-management)
- [✨ Core Features](#-core-features)
- [🔄 Workflow](#-workflow)

---

## 🎯 Overview

FivcPlayground is a multi-agent system built on the **Strands framework** that provides intelligent task assessment, dynamic tool retrieval, and flexible agent orchestration. The system uses specialized agents to handle different aspects of task execution, from initial assessment to tool generation and performance evaluation.

### Technology Stack

- **Framework**: Strands (strands-agents) - Default backend
  - **Alternative**: LangChain (langchain-core) - Optional backend
- **Web Interface**: Streamlit
- **Vector Database**: ChromaDB
- **LLM Support**: OpenAI, Ollama
- **Tool Protocol**: MCP (Model Context Protocol)

### Backend Architecture

FivcPlayground supports a **dual-backend architecture** allowing you to choose between:

1. **Strands Backend** (Default)
   - Uses `strands-agents` framework
   - Optimized for agent orchestration
   - Imported from: `fivcplayground.backends.strands`

2. **LangChain Backend** (Alternative)
   - Uses `langchain-core` framework
   - Broader ecosystem integration
   - Imported from: `fivcplayground.backends.langchain`

Backend selection is done explicitly when creating backend instances. See [Backend Selection Guide](BACKEND_SELECTION.md) for detailed instructions.

---

## 🏗️ Architecture

FivcPlayground follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│              (Streamlit Web / CLI)                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Agent Layer                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Companion │  │Consultant│  │ Planner  │  ...        │
│  └──────────┘  └──────────┘  └──────────┘             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Tool Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Calculator│  │  Python  │  │   MCP    │  ...        │
│  └──────────┘  └──────────┘  └──────────┘             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Model Layer                             │
│         (OpenAI / Ollama / Custom)                       │
└─────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Description | Location |
|-----------|-------------|----------|
| **Agents** | Specialized agents for different tasks | `src/fivcplayground/agents/` |
| **Agent Types** | Runtime models, repositories, monitors | `src/fivcplayground/agents/types/` |
| **Tools** | Tool management and retrieval system | `src/fivcplayground/tools/` |
| **Models** | LLM model factories and providers | `src/fivcplayground/models/` |
| **Tasks** | Task execution and orchestration | `src/fivcplayground/tasks/` |
| **Plays** | Streamlit web interface | `src/fivcplayground/plays/` |
| **Embeddings** | Vector database for semantic search | `src/fivcplayground/embeddings/` |
| **Settings** | Configuration management | `src/fivcplayground/settings/` |
| **Utils** | Utility functions and helpers | `src/fivcplayground/utils/` |

### Agent Runtime System

FivcPlayground includes a comprehensive runtime tracking system for agent execution:

**Core Models:**
- `AgentRunSession`: Agent configuration and metadata
- `AgentRun`: Complete execution state and history
- `AgentRunToolCall`: Individual tool invocation records
- `AgentRunStatus`: Execution status (PENDING, EXECUTING, COMPLETED, FAILED)

**Repository Pattern:**
- `AgentRunRepository`: Abstract interface for persistence
- `FileAgentRunRepository`: File-based JSON storage implementation
- `SqliteAgentRunRepository`: SQLite database-backed implementation
- Hierarchical directory structure for organized data storage (file-based)
- Relational database schema with foreign keys and indexes (SQLite)
- Automatic persistence of all agent interactions

**Storage Structure:**
```
.fivcplayground/agents/
└── agent_<agent_id>/
    ├── agent.json                    # Agent metadata
    └── run_<timestamp>/
        ├── run.json                  # Runtime execution data
        └── tool_calls/
            └── tool_call_<id>.json   # Tool call records
```

---

## 🤖 Agent System

FivcPlayground provides a flexible agent system with specialized agents for different purposes:

### Agent Types

#### 1. **Generic Agent**
*Standard agent for general task execution*
- Default agent for most tasks
- Equipped with all available tools
- Flexible and adaptable to various scenarios

#### 2. **Companion Agent**
*Friendly chat agent for conversations*
- Optimized for natural dialogue
- Uses chat-optimized LLM models
- Maintains conversation context
- Ideal for interactive sessions

#### 3. **Tooling Agent**
*Specialized in finding the right tools*
- Analyzes task requirements
- Searches tool registry
- Recommends optimal tool combinations
- Uses reasoning-optimized models

#### 4. **Consultant Agent**
*Assesses tasks and recommends approaches*
- Evaluates task complexity
- Determines if planning is needed
- Identifies required tools
- Provides direct answers for simple queries

#### 5. **Planner Agent**
*Creates execution plans and teams*
- Breaks down complex tasks
- Designs specialized agent teams
- Assigns tools to team members
- Coordinates multi-agent workflows

#### 6. **Researcher Agent**
*Analyzes patterns and workflows*
- Identifies recurring task sequences
- Analyzes execution patterns
- Extracts insights from logs
- Supports continuous improvement

#### 7. **Engineer Agent**
*Develops and optimizes tools*
- Creates composite tools
- Combines existing functionalities
- Implements new capabilities
- Maintains tool ecosystem

#### 8. **Evaluator Agent**
*Assesses performance and quality*
- Monitors agent performance
- Evaluates tool effectiveness
- Provides improvement feedback
- Validates new implementations

#### 9. **Generic Swarm**
*Multi-agent team for complex tasks*
- Coordinates multiple specialized agents
- Distributes work across team members
- Manages inter-agent communication
- Aggregates results

### Agent Creation

Agents are created using the `create_agent()` function with different `agent_config_id` values:

```python
from fivcplayground import agents

# Create a generic agent
agent = agents.create_agent()

# Create specialized agents by specifying agent_config_id
companion = agents.create_agent(agent_config_id="companion")
consultant = agents.create_agent(agent_config_id="consultant")
planner = agents.create_agent(agent_config_id="planner")
researcher = agents.create_agent(agent_config_id="researcher")
engineer = agents.create_agent(agent_config_id="engineer")
evaluator = agents.create_agent(agent_config_id="evaluator")

# Available agent config IDs:
# - "default" - Generic agent for general task execution
# - "companion" - Friendly chat agent for conversations
# - "consultant" - Assesses tasks and recommends approaches
# - "planner" - Creates execution plans and teams
# - "researcher" - Analyzes patterns and workflows
# - "engineer" - Develops and optimizes tools
# - "evaluator" - Assesses performance and quality
```

---

## 🧰 Tool Management

### Tool System

FivcPlayground uses a flexible tool management system:

**Built-in Tools:**
- `calculator` - Mathematical calculations
- `current_time` - Date and time information
- `python_repl` - Python code execution

**MCP Tools:**
- Dynamically loaded from MCP servers
- Configured via `configs/mcp.yaml`
- Supports any MCP-compatible tool

### Tool Configuration

Tool configurations are managed using the `ToolConfig` Pydantic model and `ToolConfigRepository` pattern:

```python
from fivcplayground.tools.types.base import ToolConfig
from fivcplayground.tools.types.repositories import FileToolConfigRepository

# Create a repository for storing tool configurations
repo = FileToolConfigRepository()

# Create a tool configuration
tool_config = ToolConfig(
    id="my_server",
    description="My MCP server",
    transport="stdio",  # or "sse" or "streamable_http"
    command="python",
    args=["server.py"],
    env={"VAR": "value"}  # optional
)

# Store the configuration (async)
await repo.update_tool_config_async(tool_config)

# Retrieve a configuration (async)
config = await repo.get_tool_config_async("my_server")

# List all configurations (async)
all_configs = await repo.list_tool_configs_async()

# Delete a configuration (async)
await repo.delete_tool_config_async("my_server")
```

**Configuration Types:**

The `ToolConfig` model supports two types of MCP server configurations:

1. **Command-based** (stdio):

```python
tool_config = ToolConfig(
    id="my_server",
    description="My command-based server",
    transport="stdio",
    command="python",
    args=["server.py"],
    env={"VAR": "value"}  # optional
)
```

2. **URL-based** (SSE):

```python
tool_config = ToolConfig(
    id="my_sse_server",
    description="My SSE-based server",
    transport="sse",
    url="http://localhost:8000"
)
```

**API Details:**

- `ToolConfig` - Pydantic model for tool configuration with validation
- `ToolConfigRepository` - Abstract base class for tool configuration storage
- `FileToolConfigRepository` - File-based implementation using YAML storage
- `update_tool_config_async(config)` - Stores or updates a tool configuration (async)
- `get_tool_config_async(tool_id)` - Retrieves a specific configuration (async)
- `list_tool_configs_async()` - Lists all stored configurations (async)
- `delete_tool_config_async(tool_id)` - Removes a configuration (async)

**Note**: All repository methods use async/await pattern. Deprecated synchronous methods (without `_async` suffix) are still available for backward compatibility but should be migrated to async versions.

Supported configuration formats:
- **YAML** (.yaml, .yml) - Human-readable format
- **JSON** (.json) - Machine-readable format

### Tool Retrieval

The `ToolRetriever` provides semantic search over available tools:

```python
import asyncio
from fivcplayground.tools import create_tool_retriever_async
from fivcplayground.backends.strands.tools import StrandsToolBackend

async def main():
    # Create a tool retriever with explicit backend selection
    retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend()
    )

    # Get all tools
    all_tools = await retriever.list_tools_async()

    # Get specific tools by name
    calculator = await retriever.get_tool_async("calculator")
    clock = await retriever.get_tool_async("clock")

    # Search for relevant tools using semantic search
    relevant_tools = await retriever.retrieve_tools_async("I need to calculate something")

asyncio.run(main())
```

#### Tool Bundles

Tools from MCP servers are automatically organized into **bundles** by server. When retrieving tools:

- **`expand=False` (default)**: Returns `ToolBundle` objects that group related tools from the same MCP server
- **`expand=True`**: Expands bundles and returns individual tools

This is useful for:
- **Bundle mode**: When you want to treat a server's tools as a cohesive unit
- **Expanded mode**: When you need individual tools for fine-grained control

#### Built-in Tools

FivcPlayground includes these built-in tools:
- **`calculator`** - Mathematical calculations
- **`clock`** - Current date and time information

---

## ✨ Core Features

### 1. **Intelligent Task Assessment**
- Automatic complexity evaluation
- Tool requirement identification
- Planning necessity determination
- Direct answer provision for simple queries

### 2. **Dynamic Tool Management**
- Automatic tool discovery and registration
- MCP protocol support
- Semantic tool search
- Tool combination and composition

### 3. **Flexible Agent Orchestration**
- Multiple specialized agent types
- Dynamic agent creation
- Multi-agent coordination (Swarm)
- Conversation management

### 4. **Interactive Web Interface**
- Multi-page navigation with Streamlit
- Multiple concurrent chat sessions
- Real-time streaming responses
- Async execution support
- Tool usage visualization
- Persistent conversation history
- Component-based UI architecture

### 5. **Comprehensive Persistence**
- File-based agent runtime storage
- Complete execution history tracking
- Tool call recording and replay
- JSON-based human-readable format
- Hierarchical directory organization

### 6. **Extensible Architecture**
- Plugin-based tool system
- Custom agent creation with decorators
- Multiple LLM provider support
- Modular component design
- Repository pattern for data storage
- Event-driven monitoring system

---

## 🔄 Workflow

### Basic Execution Flow

```
1. User Input
   ↓
2. Agent Selection
   ↓
3. Task Assessment (Consultant)
   ↓
4. Tool Retrieval (if needed)
   ↓
5. Execution (Generic/Specialized Agent)
   ↓
6. Result Delivery
```

### Complex Task Flow

```
1. User Input
   ↓
2. Consultant Assessment
   ↓
3. Planning Required?
   ├─ Yes → Planner Agent
   │         ↓
   │      Team Creation
   │         ↓
   │      Swarm Execution
   │         ↓
   └─ No → Direct Execution
   ↓
4. Result Aggregation
   ↓
5. Evaluation (optional)
   ↓
6. Result Delivery
```

### Tool Generation Flow (Future)

```
1. Pattern Recognition (Researcher)
   ↓
2. Tool Design (Engineer)
   ↓
3. Implementation
   ↓
4. Evaluation (Evaluator)
   ↓
5. Registration (if approved)
   ↓
6. Monitoring & Optimization
```

---

## 🏗️ Web Application Architecture

### Multi-Page Structure

FivcPlayground's web interface uses Streamlit's navigation system for a modern multi-page experience:

```
Web Application
├── Chats (Dynamic Pages)
│   ├── New Chat (Create new conversation)
│   └── Chat Pages (One per existing chat)
└── Settings
    └── Configuration & Management
```

### Component Hierarchy

```
app/__init__.py (Main Application)
├── ChatManager (Multi-chat orchestration)
│   └── Chat Instances (Individual conversations)
│       ├── AgentRunRepository (Persistence)
│       ├── ToolRetriever (Tool access)
│       └── Agent Execution (Strands agents)
├── Views (ViewBase implementations)
│   ├── base.py (ViewBase, ViewNavigation)
│   ├── ChatView.render(nav)
│   ├── SettingsView.render(nav)
│   └── TasksView.render(nav)
└── Components (Reusable UI)
    └── chat_message.render(runtime, container)
```

### Data Flow

```
User Input
    ↓
Chat View (views/chats.py)
    ↓
Chat.ask(query, on_event=callback)
    ↓
Agent Execution (async)
    ↓
Streaming Updates → on_event callback
    ↓
Component Rendering (chat_message)
    ↓
Repository Persistence (FileAgentRunRepository)
    ↓
UI Update (st.rerun)
```

---

## 🚀 Future Enhancements

- **Autonomous Tool Generation**: Automatic creation of composite tools
- **Performance Optimization**: ML-based decision optimization
- **Enhanced Evaluation**: Comprehensive performance metrics
- **Pattern Learning**: Workflow pattern recognition and optimization
- **Human-in-the-Loop**: Interactive validation and feedback
- **Task Monitoring Dashboard**: Real-time task execution visualization
- **Multi-Agent Collaboration**: Enhanced swarm coordination
- **Database Backend**: Optional database repository implementation

---

**Last Updated**: 2025-11-25
**Version**: 0.1.0
**Framework**: Strands (strands-agents 1.9.1+) / LangChain (langchain-core 0.3+)
