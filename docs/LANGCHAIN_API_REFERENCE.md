# LangChain API Reference

## 📚 Overview

This document provides a complete API reference for the LangChain-based FivcPlayground system. All APIs maintain 100% backward compatibility with the Strands framework.

---

## 🤖 Agent API

### Creating Agents

#### `create_companion_agent()`
Creates a companion agent for general conversation.

```python
from fivcplayground.agents import create_companion_agent

agent = create_companion_agent()
result = await agent.invoke_async("Hello!")
```

**Returns**: `LangChainAgentAdapter`

**Methods**:
- `invoke(query: str) -> str` - Synchronous invocation
- `invoke_async(query: str) -> str` - Asynchronous invocation
- `invoke_with_tools(query: str, tools: List[AgentTool]) -> str` - With custom tools

---

#### `create_tooling_agent()`
Creates an agent specialized in tool retrieval and usage.

```python
from fivcplayground.agents import create_tooling_agent

agent = create_tooling_agent()
result = await agent.invoke_async("Find tools for data analysis")
```

**Returns**: `LangChainAgentAdapter`

---

#### `create_consultant_agent()`
Creates a consultant agent for expert advice.

```python
from fivcplayground.agents import create_consultant_agent

agent = create_consultant_agent()
result = await agent.invoke_async("What's the best approach for this?")
```

**Returns**: `LangChainAgentAdapter`

---

#### `create_planning_agent()`
Creates a planning agent for task planning.

```python
from fivcplayground.agents import create_planning_agent

agent = create_planning_agent()
result = await agent.invoke_async("Plan my project")
```

**Returns**: `LangChainAgentAdapter`

---

#### `create_research_agent()`
Creates a research agent for information gathering.

```python
from fivcplayground.agents import create_research_agent

agent = create_research_agent()
result = await agent.invoke_async("Research machine learning")
```

**Returns**: `LangChainAgentAdapter`

---

### Agent Methods

#### `invoke(query: str) -> str`
Synchronous agent invocation.

```python
result = agent.invoke("What is AI?")
print(result)  # Agent response
```

**Parameters**:
- `query` (str): The input query

**Returns**: Agent response as string

**Raises**: `RuntimeError` if agent fails

---

#### `invoke_async(query: str) -> str`
Asynchronous agent invocation.

```python
result = await agent.invoke_async("What is AI?")
print(result)  # Agent response
```

**Parameters**:
- `query` (str): The input query

**Returns**: Agent response as string (awaitable)

**Raises**: `RuntimeError` if agent fails

---

#### `invoke_with_tools(query: str, tools: List[AgentTool]) -> str`
Invocation with custom tools.

```python
from fivcplayground.tools.types import AgentTool

tools = [
    AgentTool(
        tool_name="calculator",
        tool_spec={"description": "Performs calculations"},
        func=lambda x: eval(x)
    )
]

result = agent.invoke_with_tools("Calculate 2+2", tools)
```

**Parameters**:
- `query` (str): The input query
- `tools` (List[AgentTool]): Custom tools to use

**Returns**: Agent response as string

---

### Agent Properties

#### `name: str`
Agent name.

```python
print(agent.name)  # "CompanionAgent"
```

---

#### `model: BaseLanguageModel`
The underlying LLM model.

```python
print(agent.model)  # ChatOpenAI or ChatOllama
```

---

#### `tools: List[StructuredTool]`
List of available tools.

```python
for tool in agent.tools:
    print(tool.name)
```

---

#### `event_bus: EventBus`
Event bus for subscribing to agent events.

```python
def on_event(event):
    print(f"Event: {event.event_type}")

agent.event_bus.subscribe("BEFORE_INVOCATION", on_event)
```

---

## 🛠️ Tool API

### Tool Types

#### `AgentTool`
Represents a tool that agents can use.

```python
from fivcplayground.tools.types import AgentTool

tool = AgentTool(
    tool_name="my_tool",
    tool_spec={
        "description": "Does something useful",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            }
        }
    },
    func=lambda x: f"Result: {x}"
)
```

**Attributes**:
- `tool_name` (str): Tool name
- `tool_spec` (dict): Tool specification
- `func` (callable): Tool function

---

### Tool Conversion

#### `convert_strands_tools_to_langchain(tools: List[AgentTool]) -> List[StructuredTool]`
Converts Strands tools to LangChain tools.

```python
from fivcplayground.adapters.tools import convert_strands_tools_to_langchain

strands_tools = [...]
langchain_tools = convert_strands_tools_to_langchain(strands_tools)
```

**Parameters**:
- `tools` (List[AgentTool]): Strands tools

**Returns**: List of LangChain StructuredTool objects

---

## 📡 Event API

### Event Bus

#### `EventBus`
Manages event subscriptions and emissions.

```python
from fivcplayground.adapters.events import EventBus

event_bus = EventBus()

def on_event(event):
    print(f"Event: {event.event_type}")

event_bus.subscribe("BEFORE_INVOCATION", on_event)
event_bus.emit("BEFORE_INVOCATION", {"query": "test"})
```

**Methods**:
- `subscribe(event_type: str, callback: Callable)` - Subscribe to event
- `emit(event_type: str, data: dict)` - Emit event
- `unsubscribe(event_type: str, callback: Callable)` - Unsubscribe

---

### Event Types

**BEFORE_INVOCATION**: Emitted before agent invocation
**AFTER_INVOCATION**: Emitted after agent invocation
**TOOL_CALL**: Emitted when tool is called
**ERROR**: Emitted on error

---

## 🔧 Model API

### Creating Models

#### `create_openai_model(api_key: str, model: str = "gpt-4") -> ChatOpenAI`
Creates an OpenAI model.

```python
from fivcplayground.adapters.models import create_openai_model

model = create_openai_model(api_key="sk-...", model="gpt-4")
```

**Parameters**:
- `api_key` (str): OpenAI API key
- `model` (str): Model name (default: "gpt-4")

**Returns**: ChatOpenAI instance

---

#### `create_ollama_model(base_url: str, model: str = "llama2") -> ChatOllama`
Creates an Ollama model.

```python
from fivcplayground.adapters.models import create_ollama_model

model = create_ollama_model(base_url="http://localhost:11434", model="llama2")
```

**Parameters**:
- `base_url` (str): Ollama base URL
- `model` (str): Model name (default: "llama2")

**Returns**: ChatOllama instance

---

## 📊 Configuration

### Environment Variables

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# LiteLLM
LITELLM_API_KEY=...
```

---

## ✅ Backward Compatibility

All APIs maintain 100% backward compatibility with Strands:

```python
# Old Strands code works unchanged
from fivcplayground.agents import create_companion_agent

agent = create_companion_agent()
result = await agent.invoke_async("Hello!")
```

---

## 🔗 Related Documentation

- [LangChain Migration Guide](LANGCHAIN_MIGRATION_GUIDE.md)
- [LangChain Docs](https://python.langchain.com/)
- [API Examples](../tests/test_langchain_integration.py)

---

**Last Updated**: 2025-10-24
**Status**: ✅ Complete
**Compatibility**: 100% backward compatible

