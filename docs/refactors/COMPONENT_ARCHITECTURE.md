# Component Architecture & Interaction Patterns

**Purpose**: Detailed component interaction and architecture patterns  
**Status**: Design Reference  
**Last Updated**: 2025-11-14

---

## 🏗️ Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Streamlit App, CLI, API)                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Dependency Injection Layer                      │
│  (ComponentSite, Service Locator)                           │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬──────────────┐
        │            │            │              │
┌───────▼──┐  ┌──────▼──┐  ┌─────▼──┐  ┌──────▼──┐
│Agents    │  │Models   │  │Tools   │  │Tasks    │
│Layer     │  │Layer    │  │Layer   │  │Layer    │
└───────┬──┘  └──────┬──┘  └─────┬──┘  └──────┬──┘
        │            │            │            │
┌───────▼──────────────────────────────────────▼──┐
│         Interface Layer (IComponent)             │
│  - IAgentsRuntimeRepository                     │
│  - IModelProvider                               │
│  - IToolsRepository                             │
│  - ITaskRuntimeRepository                       │
│  - IEmbeddingProvider                           │
└───────┬──────────────────────────────────────┬──┘
        │                                      │
┌───────▼──────────────────────────────────────▼──┐
│      Implementation Layer (Concrete Classes)     │
│  - FileAgentsRuntimeRepository                  │
│  - SqliteAgentsRuntimeRepository                │
│  - OpenAIModelProvider                          │
│  - OllamaModelProvider                          │
│  - InMemoryToolsRepository                      │
│  - FileToolsRepository                          │
└──────────────────────────────────────────────────┘
```

---

## 🔄 Component Interaction Patterns

### Pattern 1: Repository Pattern

```
Application
    │
    ├─ Requests data
    │
    ▼
IAgentsRuntimeRepository (Interface)
    │
    ├─ Defines contract
    │
    ▼
Concrete Implementation
    ├─ FileAgentsRuntimeRepository
    ├─ SqliteAgentsRuntimeRepository
    └─ MultiTenantAgentsRuntimeRepository (Future)
    │
    ▼
Storage Backend
    ├─ File System
    ├─ SQLite Database
    └─ Cloud Storage (Future)
```

### Pattern 2: Provider Registry Pattern

```
Application
    │
    ├─ Requests model creation
    │
    ▼
IModelProvider (Interface)
    │
    ├─ Defines contract
    │
    ▼
ModelProviderRegistry (Concrete)
    │
    ├─ Maintains provider map
    │
    ▼
Registered Providers
    ├─ OpenAIModelProvider
    ├─ OllamaModelProvider
    └─ LocalModelProvider
    │
    ▼
Model Instances
    ├─ ChatOpenAI
    ├─ ChatOllama
    └─ LocalLLM
```

### Pattern 3: Factory Pattern

```
Application
    │
    ├─ Requests component
    │
    ▼
ComponentSite (Service Locator)
    │
    ├─ Looks up interface
    │
    ▼
Registered Implementation
    │
    ├─ Creates instance
    │
    ▼
Component Instance
```

---

## 📊 Data Flow Examples

### Example 1: Agent Execution with Repository

```
ChatManager
    │
    ├─ Receives user query
    │
    ▼
Resolve IAgentsRuntimeRepository
    │
    ├─ Gets SqliteAgentsRuntimeRepository
    │
    ▼
Create AgentsRuntime
    │
    ├─ Execute agent
    │
    ▼
Update Runtime State
    │
    ├─ Calls repository.update_agent_runtime()
    │
    ▼
SQLite Database
    │
    ├─ Persists data
    │
    ▼
Return to UI
```

### Example 2: Model Creation with Provider Registry

```
Agent Creation
    │
    ├─ Needs LLM model
    │
    ▼
Resolve IModelProvider
    │
    ├─ Gets ModelProviderRegistry
    │
    ▼
Call create_model(provider="openai")
    │
    ├─ Registry looks up "openai"
    │
    ▼
OpenAIModelProvider.create_model()
    │
    ├─ Creates ChatOpenAI instance
    │
    ▼
Return Model
    │
    ├─ Agent uses model
    │
    ▼
Execute Agent
```

### Example 3: Tool Retrieval with Repository

```
Agent Execution
    │
    ├─ Needs tools
    │
    ▼
Resolve IToolsRepository
    │
    ├─ Gets InMemoryToolsRepository
    │
    ▼
Call list_tools()
    │
    ├─ Returns all registered tools
    │
    ▼
Filter Tools
    │
    ├─ Select relevant tools
    │
    ▼
Pass to Agent
    │
    ├─ Agent uses tools
    │
    ▼
Execute Tool Calls
```

---

## 🔌 Interface Contracts

### IAgentsRuntimeRepository Contract

**Responsibilities:**
- Persist agent metadata
- Store agent execution runtimes
- Track tool calls within runtimes
- Support CRUD operations
- Maintain referential integrity

**Guarantees:**
- Idempotent updates
- Cascading deletes
- Consistent state
- Thread-safe operations

### IModelProvider Contract

**Responsibilities:**
- Create model instances
- Manage provider registry
- Handle provider configuration
- Support multiple providers

**Guarantees:**
- Consistent model interface
- Provider validation
- Configuration merging
- Error handling

### IToolsRepository Contract

**Responsibilities:**
- Store tools
- Retrieve tools by name
- List all tools
- Support tool metadata

**Guarantees:**
- Fast lookups
- Consistent tool interface
- Metadata preservation
- Efficient iteration

---

## 🎯 Component Lifecycle

### Initialization Phase

```
1. Application Start
   │
   ├─ Load Configuration
   │
   ├─ Create ComponentSite
   │
   ├─ Register Implementations
   │   ├─ IAgentsRuntimeRepository → SqliteAgentsRuntimeRepository
   │   ├─ IModelProvider → ModelProviderRegistry
   │   ├─ IToolsRepository → InMemoryToolsRepository
   │   └─ IEmbeddingProvider → EmbeddingProviderRegistry
   │
   ├─ Initialize Components
   │
   └─ Ready for Use
```

### Runtime Phase

```
1. Request Component
   │
   ├─ Resolve from ComponentSite
   │
   ├─ Use Component
   │
   ├─ Component Performs Operations
   │
   └─ Return Results
```

### Shutdown Phase

```
1. Application Shutdown
   │
   ├─ Cleanup Components
   │   ├─ Close database connections
   │   ├─ Flush pending writes
   │   └─ Release resources
   │
   ├─ Unregister Components
   │
   └─ Shutdown Complete
```

---

## 🔐 Dependency Resolution Strategy

### Strategy 1: Constructor Injection

```python
class ChatManager:
    def __init__(self, repo: IAgentsRuntimeRepository):
        self.repo = repo
```

### Strategy 2: Service Locator

```python
class ChatManager:
    def __init__(self):
        self.repo = resolve(IAgentsRuntimeRepository)
```

### Strategy 3: Hybrid Approach

```python
class ChatManager:
    def __init__(self, repo: Optional[IAgentsRuntimeRepository] = None):
        self.repo = repo or resolve(IAgentsRuntimeRepository)
```

**Recommendation**: Use Constructor Injection for testability, with Service Locator as fallback.

---

## 🧪 Testing Architecture

### Unit Testing

```
Test
    │
    ├─ Create Mock Implementation
    │
    ├─ Inject Mock
    │
    ├─ Execute Test
    │
    └─ Verify Behavior
```

### Integration Testing

```
Test
    │
    ├─ Create ComponentSite
    │
    ├─ Register Test Implementations
    │
    ├─ Execute Test
    │
    └─ Verify Integration
```

### End-to-End Testing

```
Test
    │
    ├─ Use Real ComponentSite
    │
    ├─ Use Real Implementations
    │
    ├─ Execute Full Workflow
    │
    └─ Verify Results
```

---

## 📈 Scalability Considerations

### Horizontal Scaling

- **Stateless Components**: All components should be stateless
- **Shared Storage**: Use centralized database for repositories
- **Load Balancing**: Multiple instances can share same backend

### Vertical Scaling

- **Caching**: Add caching layer for frequently accessed data
- **Connection Pooling**: Reuse database connections
- **Lazy Loading**: Load components on demand

### Multi-Tenancy

- **Tenant Isolation**: Implement tenant-aware repositories
- **Data Segregation**: Separate data by tenant
- **Configuration Per Tenant**: Different settings per tenant

---

## 🔄 Extension Points

### Adding New Repository Implementation

1. Create class implementing `IAgentsRuntimeRepository`
2. Implement all abstract methods
3. Register in ComponentSite
4. Write tests
5. Update documentation

### Adding New Model Provider

1. Create class implementing `IModelProvider`
2. Register in ModelProviderRegistry
3. Implement provider logic
4. Write tests
5. Update documentation

### Adding New Tool Repository

1. Create class implementing `IToolsRepository`
2. Implement all abstract methods
3. Register in ComponentSite
4. Write tests
5. Update documentation

