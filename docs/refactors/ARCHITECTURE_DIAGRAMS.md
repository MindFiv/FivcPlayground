# Architecture Diagrams & Visual References

**Purpose**: Visual representations of the interface-based architecture  
**Status**: Design Reference  
**Format**: ASCII diagrams and Mermaid charts

---

## 🏗️ Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Streamlit    │  │ CLI          │  │ API          │           │
│  │ Web App      │  │ Commands     │  │ Endpoints    │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Dependency Injection Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ ComponentSite (Service Locator)                          │  │
│  │  - Registers implementations                             │  │
│  │  - Resolves interfaces to implementations                │  │
│  │  - Manages component lifecycle                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────┬──────────────┐
        │                    │                │              │
┌───────▼──────┐  ┌──────────▼──────┐  ┌─────▼──────┐  ┌───▼────────┐
│ Agents       │  │ Models          │  │ Tools      │  │ Tasks      │
│ Layer        │  │ Layer           │  │ Layer      │  │ Layer      │
└───────┬──────┘  └──────────┬──────┘  └─────┬──────┘  └───┬────────┘
        │                    │                │            │
┌───────▼────────────────────▼────────────────▼────────────▼──────┐
│              Interface Layer (IComponent)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ IAgentsRuntimeRepository                                 │  │
│  │ IModelProvider                                           │  │
│  │ IToolsRepository                                         │  │
│  │ ITaskRuntimeRepository                                   │  │
│  │ IEmbeddingProvider                                       │  │
│  │ IConfigProvider                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────┬────────────────────┬────────────────┬──────────────┬────┘
        │                    │                │              │
┌───────▼──────┐  ┌──────────▼──────┐  ┌─────▼──────┐  ┌───▼────────┐
│ File         │  │ OpenAI          │  │ Memory     │  │ SQLite     │
│ Repository   │  │ Model Provider  │  │ Tools Repo │  │ Repository │
│              │  │                 │  │            │  │            │
│ SQLite       │  │ Ollama          │  │ File       │  │ File       │
│ Repository   │  │ Model Provider  │  │ Tools Repo │  │ Repository │
└──────────────┘  └─────────────────┘  └────────────┘  └────────────┘
        │                    │                │              │
        └────────────────────┼────────────────┴──────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              Storage & External Services Layer                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ File System  │  │ SQLite DB    │  │ LLM APIs     │          │
│  │              │  │              │  │ (OpenAI,     │          │
│  │              │  │              │  │  Ollama)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Component Registration Flow

```
Application Start
    │
    ├─ Load Configuration
    │   ├─ Read environment variables
    │   ├─ Read settings.yaml
    │   └─ Parse CLI arguments
    │
    ├─ Create ComponentSite
    │   └─ Initialize service locator
    │
    ├─ Register Implementations
    │   ├─ IAgentsRuntimeRepository
    │   │   └─ SqliteAgentsRuntimeRepository()
    │   ├─ IModelProvider
    │   │   └─ ModelProviderRegistry()
    │   ├─ IToolsRepository
    │   │   └─ InMemoryToolsRepository()
    │   ├─ ITaskRuntimeRepository
    │   │   └─ SqliteTaskRuntimeRepository()
    │   └─ IEmbeddingProvider
    │       └─ EmbeddingProviderRegistry()
    │
    ├─ Initialize Components
    │   ├─ Create database connections
    │   ├─ Load configurations
    │   └─ Warm up caches
    │
    └─ Ready for Use
```

---

## 🔌 Dependency Resolution Pattern

```
Request Component
    │
    ├─ resolve(IAgentsRuntimeRepository)
    │
    ├─ ComponentSite.get_component(IAgentsRuntimeRepository)
    │
    ├─ Lookup in registry
    │   ├─ Found: SqliteAgentsRuntimeRepository
    │   └─ Return instance
    │
    └─ Use Component
        ├─ repo.update_agent(agent)
        ├─ repo.get_agent(agent_id)
        └─ repo.list_agents()
```

---

## 📊 Interface Implementation Matrix

```
┌──────────────────────┬──────────────┬──────────────┬──────────────┐
│ Interface            │ Implementation 1 │ Implementation 2 │ Future   │
├──────────────────────┼──────────────┼──────────────┼──────────────┤
│ IAgentsRuntime       │ File         │ SQLite       │ Cloud        │
│ Repository           │ Repository   │ Repository   │ Repository   │
├──────────────────────┼──────────────┼──────────────┼──────────────┤
│ IModelProvider       │ OpenAI       │ Ollama       │ Anthropic    │
│                      │ Provider     │ Provider     │ Provider     │
├──────────────────────┼──────────────┼──────────────┼──────────────┤
│ IToolsRepository     │ Memory       │ File         │ Database     │
│                      │ Repository   │ Repository   │ Repository   │
├──────────────────────┼──────────────┼──────────────┼──────────────┤
│ ITaskRuntime         │ File         │ SQLite       │ Distributed  │
│ Repository           │ Repository   │ Repository   │ Repository   │
├──────────────────────┼──────────────┼──────────────┼──────────────┤
│ IEmbeddingProvider   │ OpenAI       │ Ollama       │ HuggingFace  │
│                      │ Provider     │ Provider     │ Provider     │
└──────────────────────┴──────────────┴──────────────┴──────────────┘
```

---

## 🔄 Agent Execution Flow with DI

```
User Query
    │
    ├─ ChatManager.add_message(query)
    │
    ├─ Resolve IAgentsRuntimeRepository
    │   └─ Get SqliteAgentsRuntimeRepository
    │
    ├─ Create AgentsRuntime
    │   └─ repo.update_agent_runtime(runtime)
    │
    ├─ Resolve IModelProvider
    │   └─ Get ModelProviderRegistry
    │
    ├─ Create Model
    │   └─ provider.create_model(provider="openai")
    │
    ├─ Resolve IToolsRepository
    │   └─ Get InMemoryToolsRepository
    │
    ├─ Get Tools
    │   └─ tools_repo.list_tools()
    │
    ├─ Execute Agent
    │   ├─ Agent uses model
    │   ├─ Agent uses tools
    │   └─ Agent generates response
    │
    ├─ Update Runtime
    │   └─ repo.update_agent_runtime(runtime)
    │
    └─ Return Response to UI
```

---

## 🧪 Testing Architecture

```
Test Suite
    │
    ├─ Unit Tests
    │   ├─ Test Interface Contracts
    │   ├─ Test Individual Implementations
    │   └─ Use Mock Implementations
    │
    ├─ Integration Tests
    │   ├─ Test Component Registration
    │   ├─ Test Component Resolution
    │   ├─ Test with Different Implementations
    │   └─ Use Real Implementations
    │
    ├─ End-to-End Tests
    │   ├─ Test Full Workflows
    │   ├─ Test with Real Data
    │   └─ Test Performance
    │
    └─ Backward Compatibility Tests
        ├─ Test Old Code Still Works
        ├─ Test Migration Paths
        └─ Test Deprecation Warnings
```

---

## 📁 Directory Structure

```
src/fivcplayground/
├── interfaces/                    ← NEW: Interface definitions
│   ├── __init__.py
│   ├── repositories.py           ← IAgentsRuntimeRepository, ITaskRuntimeRepository
│   ├── models.py                 ← IModelProvider
│   ├── tools.py                  ← IToolsRepository
│   ├── embeddings.py             ← IEmbeddingProvider
│   └── config.py                 ← IConfigProvider
│
├── agents/
│   └── types/
│       └── repositories/
│           ├── base.py           ← REFACTORED: Now imports from interfaces
│           ├── files.py          ← FileAgentsRuntimeRepository
│           └── sqlite.py         ← SqliteAgentsRuntimeRepository
│
├── models/
│   ├── providers/                ← NEW: Provider implementations
│   │   ├── __init__.py
│   │   ├── base.py              ← IModelProvider
│   │   ├── registry.py          ← ModelProviderRegistry
│   │   ├── openai.py            ← OpenAIModelProvider
│   │   └── ollama.py            ← OllamaModelProvider
│   └── backends/
│       ├── langchain.py
│       └── strands.py
│
├── tools/
│   └── types/
│       └── repositories/         ← NEW: Tool repositories
│           ├── __init__.py
│           ├── base.py          ← IToolsRepository
│           ├── memory.py        ← InMemoryToolsRepository
│           └── file.py          ← FileToolsRepository
│
├── tasks/
│   └── types/
│       └── repositories/         ← NEW: Task repositories
│           ├── __init__.py
│           ├── base.py          ← ITaskRuntimeRepository
│           ├── file.py          ← FileTaskRuntimeRepository
│           └── sqlite.py        ← SqliteTaskRuntimeRepository
│
├── embeddings/
│   └── types/
│       └── providers/            ← NEW: Embedding providers
│           ├── __init__.py
│           ├── base.py          ← IEmbeddingProvider
│           ├── registry.py      ← EmbeddingProviderRegistry
│           ├── openai.py        ← OpenAIEmbeddingProvider
│           └── ollama.py        ← OllamaEmbeddingProvider
│
├── settings/
│   ├── __init__.py              ← REFACTORED: Enhanced with DI
│   └── types/
│       └── config.py            ← REFACTORED: Enhanced with provider pattern
│
├── app/
│   ├── __init__.py              ← REFACTORED: Use DI for component resolution
│   └── utils/
│       └── chats.py             ← REFACTORED: Accept interface types
│
└── utils/
    ├── di.py                    ← NEW: DI utilities
    └── types/
        └── ...
```

---

## 🔐 Security & Multi-Tenancy

```
Multi-Tenant Architecture
    │
    ├─ Tenant Context
    │   ├─ Tenant ID
    │   ├─ User ID
    │   └─ Permissions
    │
    ├─ Tenant-Aware Repository
    │   ├─ Filter by tenant
    │   ├─ Enforce isolation
    │   └─ Audit access
    │
    ├─ Tenant-Specific Configuration
    │   ├─ Model provider per tenant
    │   ├─ Storage backend per tenant
    │   └─ Tools available per tenant
    │
    └─ Tenant-Isolated Data
        ├─ Separate databases
        ├─ Separate file systems
        └─ Separate caches
```

---

## 🚀 Deployment Scenarios

### Scenario 1: Single-Tenant Development

```
Developer Machine
    │
    ├─ ComponentSite
    │   ├─ FileAgentsRuntimeRepository
    │   ├─ OllamaModelProvider
    │   └─ InMemoryToolsRepository
    │
    └─ Local Storage
        ├─ File system
        └─ Local LLM
```

### Scenario 2: Multi-Tenant Production

```
Production Environment
    │
    ├─ Load Balancer
    │   └─ Multiple App Instances
    │
    ├─ ComponentSite (Shared)
    │   ├─ SqliteAgentsRuntimeRepository (Shared DB)
    │   ├─ OpenAIModelProvider
    │   └─ DatabaseToolsRepository (Shared DB)
    │
    └─ Shared Storage
        ├─ PostgreSQL Database
        ├─ Redis Cache
        └─ S3 File Storage
```

### Scenario 3: Microservices

```
Microservices Architecture
    │
    ├─ Agent Service
    │   ├─ ComponentSite
    │   └─ IAgentsRuntimeRepository
    │
    ├─ Model Service
    │   ├─ ComponentSite
    │   └─ IModelProvider
    │
    ├─ Tools Service
    │   ├─ ComponentSite
    │   └─ IToolsRepository
    │
    └─ Shared Services
        ├─ Database
        ├─ Cache
        └─ Message Queue
```

---

## 📈 Scalability Patterns

```
Horizontal Scaling
    │
    ├─ Stateless Components
    │   └─ No local state
    │
    ├─ Shared Storage
    │   ├─ Centralized database
    │   ├─ Distributed cache
    │   └─ Shared file storage
    │
    ├─ Load Balancing
    │   └─ Route requests to instances
    │
    └─ Auto-Scaling
        ├─ Scale up on demand
        └─ Scale down when idle
```

