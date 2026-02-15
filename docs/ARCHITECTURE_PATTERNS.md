# Architecture Patterns Guide

FivcPlayground uses a **fivcglue interface-based architecture** pattern for flexible component substitution and dependency injection. This guide explains the core patterns used throughout the codebase.

## 🏗️ Core Patterns

### 1. Repository Pattern

**Purpose**: Abstract data persistence from business logic

**Structure**:
```python
# Abstract interface with async methods
class AgentConfigRepository(ABC):
    @abstractmethod
    async def get_agent_config_async(self, agent_id: str) -> AgentConfig | None:
        """Retrieve an agent configuration by ID."""
        pass

# Concrete implementation
class FileAgentConfigRepository(AgentConfigRepository):
    async def get_agent_config_async(self, agent_id: str) -> AgentConfig | None:
        # File-based implementation
        pass
```

**Benefits**:
- Easy to swap implementations (file, database, cloud)
- Testable with mock repositories
- Consistent interface across components
- Async/await support for non-blocking I/O operations

**Used for**:
- Agent configurations
- Model configurations
- Tool configurations
- Embedding configurations
- Agent run history

**Note**: All repository methods use async/await pattern. Deprecated synchronous methods are still available for backward compatibility but should be migrated to async versions.

### 2. Factory Pattern

**Purpose**: Create instances with complex initialization

**Structure**:
```python
async def create_tool_retriever_async(
    tool_backend: ToolBackend | None = None,
    tool_config_repository: ToolConfigRepository | None = None,
    embedding_backend: EmbeddingBackend | None = None,
    embedding_config_repository: EmbeddingConfigRepository | None = None,
    embedding_config_id: str = "default",
) -> ToolRetriever | None:
    # Complex initialization logic
    embedding_db = await create_embedding_db_async(...)
    retriever = ToolRetriever(
        tool_backend=tool_backend,
        tool_config_repository=tool_config_repository,
        embedding_db=embedding_db,
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

### 5. Structured Output Pattern

**Purpose**: Enable type-safe, structured data extraction from LLM responses using Pydantic models

**Problem**: Agents need to return structured data (not just text) for integration with downstream systems, databases, and APIs. Manual parsing of text responses is error-prone and fragile.

**Solution**: Store structured output alongside text in `AgentRunContent`:

```python
class AgentRunContent(BaseModel):
    text: str | None = None
    structured: dict[str, Any] | None = None  # JSON-serializable dict
    images: list[str] | None = None
    files: list[str] | None = None
```

**Implementation Flow**:

1. **Configuration**: Define response schema (JSON Schema in agent config → Pydantic model via `SchemaConverter`)
2. **Execution**: Backend extracts structured output from framework response
3. **Storage**: Serialize Pydantic model to dict via `model_dump(mode="json")`
4. **Return**: Return Pydantic instance for immediate use; persist dict for later retrieval

**Backend Parity**:

Both Strands and LangChain backends follow identical patterns:

**Strands Backend** (`backends/strands/agents.py:286-310`):
```python
# Extract structured output from StrandsAgentResult
agent_run_reply_structured = output.structured_output

# Store both text and structured data
agent_run.reply = AgentRunContent(
    text=str(output),
    structured=(
        agent_run_reply_structured.model_dump(mode="json") if
        agent_run_reply_structured else None
    ),
)

# Return Pydantic instance when available, otherwise AgentRunContent
return (
    agent_run_reply_structured if
    agent_run_reply_structured else agent_run.reply
)
```

**LangChain Backend** (`backends/langchain/agents.py:251-283`):
```python
# Extract structured output from agent outputs
agent_run_reply_structured = None
if "structured_response" in outputs:
    structured_output = outputs["structured_response"]
    if isinstance(structured_output, BaseModel):
        agent_run_reply_structured = structured_output

# Store both text and structured data
if "messages" in outputs:
    output = outputs["messages"][-1]
    agent_run.reply = AgentRunContent(
        text=output.content,
        structured=(
            agent_run_reply_structured.model_dump(mode="json") if
            agent_run_reply_structured else None
        ),
    )

# Return Pydantic instance when available, otherwise AgentRunContent
return (
    agent_run_reply_structured if
    agent_run_reply_structured else agent_run.reply
)
```

**Usage Example**:

```python
from pydantic import BaseModel, EmailStr
from fivcplayground.agents import create_agent_async

class ContactInfo(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None

# Runtime approach: Pass Pydantic model
agent = await create_agent_async("data_extractor")
result = await agent.run_async(
    query="Extract: John Doe, john@example.com, +1-555-0100",
    response_model=ContactInfo
)

# Result is a typed Pydantic instance
assert isinstance(result, ContactInfo)
print(result.name)   # "John Doe"
print(result.email)  # "john@example.com"

# Structured data is also persisted in agent_run.reply.structured
agent_run = await repo.get_agent_run_async(session_id, result.id)
assert agent_run.reply.structured == {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0100"
}
```

**Benefits**:
- **Type Safety**: Pydantic validation ensures data conforms to schema
- **Dual Storage**: Structured data (for code) + text (for humans/UI)
- **Backend Agnostic**: Works identically with Strands and LangChain
- **Automatic Persistence**: Repositories serialize/deserialize transparently
- **Developer Experience**: IntelliSense, type hints, and validation errors

**Testing Strategy**:
- Unit tests verify serialization/deserialization round-trips
- Integration tests verify backend parity (both produce identical output)
- Persistence tests verify file and SQLite repositories handle structured field
- See `tests/test_agent_structured_output.py` for comprehensive test suite

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

