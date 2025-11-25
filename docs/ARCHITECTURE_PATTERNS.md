# Architecture Patterns Guide

FivcPlayground uses a **fivcglue interface-based architecture** pattern for flexible component substitution and dependency injection. This guide explains the core patterns used throughout the codebase.

## 🏗️ Core Patterns

### 1. Repository Pattern

**Purpose**: Abstract data persistence from business logic

**Structure**:
```python
# Abstract interface
class AgentConfigRepository(ABC):
    @abstractmethod
    def get_agent_config(self, agent_id: str) -> AgentConfig | None:
        pass

# Concrete implementation
class FileAgentConfigRepository(AgentConfigRepository):
    def get_agent_config(self, agent_id: str) -> AgentConfig | None:
        # File-based implementation
        pass
```

**Benefits**:
- Easy to swap implementations (file, database, cloud)
- Testable with mock repositories
- Consistent interface across components

**Used for**:
- Agent configurations
- Model configurations
- Tool configurations
- Embedding configurations
- Agent run history

### 2. Factory Pattern

**Purpose**: Create instances with complex initialization

**Structure**:
```python
def create_tool_retriever(
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
) -> ToolRetriever:
    retriever = ToolRetriever(
        embedding_config_repository=embedding_config_repository,
        embedding_config_id=embedding_config_id,
    )
    return retriever
```

**Benefits**:
- Encapsulates complex creation logic
- Provides sensible defaults
- Easy to extend with new options

### 3. Dependency Injection

**Purpose**: Decouple components through constructor injection

**Structure**:
```python
class Chat:
    def __init__(
        self,
        agent_run_repository: AgentRunRepository,
        tool_retriever: ToolRetriever,
        model_config_repository: ModelConfigRepository,
    ):
        self.agent_run_repository = agent_run_repository
        self.tool_retriever = tool_retriever
        self.model_config_repository = model_config_repository
```

**Benefits**:
- Loose coupling between components
- Easy to test with mock dependencies
- Flexible configuration

### 4. Configuration Management

**Purpose**: Centralized configuration with validation

**Structure**:
```python
class ModelConfig(BaseModel):
    id: str
    provider: str
    model: str
    api_key: str | None
    temperature: float = 0.5
```

**Benefits**:
- Type-safe configuration
- Automatic validation
- Easy serialization/deserialization

## 📦 Component Organization

### Layered Architecture

```
┌─────────────────────────────────────┐
│  Application Layer (app/)           │
│  - Streamlit UI                     │
│  - CLI commands                     │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Business Logic Layer               │
│  - Agents (agents/)                 │
│  - Tasks (tasks/)                   │
│  - Tool Management (tools/)         │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Data Layer                         │
│  - Repositories (*/repositories/)   │
│  - Models (*/types/base.py)         │
│  - Embeddings (embeddings/)         │
└─────────────────────────────────────┘
```

## 🔄 Data Flow Example

### Agent Execution Flow

```
1. User Input (Web/CLI)
   ↓
2. Chat/Agent Manager
   ├─ Load agent config (AgentConfigRepository)
   ├─ Load model config (ModelConfigRepository)
   └─ Get tools (ToolRetriever)
   ↓
3. Agent Execution
   ├─ Create agent instance
   ├─ Execute with tools
   └─ Stream results
   ↓
4. Persistence
   ├─ Save run (AgentRunRepository)
   ├─ Save tool calls
   └─ Update history
   ↓
5. UI Update
```

## 🎯 Design Principles

1. **Separation of Concerns** - Each component has a single responsibility
2. **Dependency Inversion** - Depend on abstractions, not concrete implementations
3. **Open/Closed Principle** - Open for extension, closed for modification
4. **Interface Segregation** - Clients depend only on interfaces they use
5. **DRY (Don't Repeat Yourself)** - Reuse common patterns

---

**Last Updated**: 2025-11-25
**Version**: 0.1.0

