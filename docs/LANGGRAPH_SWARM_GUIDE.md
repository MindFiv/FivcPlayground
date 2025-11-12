# LangGraph Swarm Integration Guide

## Overview

FivcPlayground now uses **LangGraph Swarm** for multi-agent orchestration, replacing the previous Strands Swarm implementation. This guide explains how to use the swarm system in your applications.

## Key Features

- **Multi-Agent Orchestration**: Coordinate multiple specialized agents
- **Dynamic Handoffs**: Agents can hand off tasks to each other based on specialization
- **Backward Compatible**: Maintains the same API as Strands Swarm
- **LangChain Integration**: Built on top of LangChain 0.3.x and LangGraph 0.6.x
- **Async Support**: Full async/await support for non-blocking operations

## Installation

The swarm system is included in FivcPlayground. Ensure you have the required dependencies:

```bash
pip install -e .
```

This installs:
- `langchain>=0.3.0`
- `langchain-core>=0.3.0`
- `langchain-community>=0.3.0`
- `langchain-openai>=0.2.0`
- `langgraph>=0.6.0,<0.7.0`
- `langgraph-swarm>=0.0.14`

## Quick Start

### Creating a Swarm

```python
from fivcplayground.adapters import create_langchain_swarm
from fivcplayground.agents import create_default_agent
from langchain_openai import ChatOpenAI

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# Create agents
agent1 = create_default_agent(
    model=llm,
    tools=[...],
    system_prompt="You are Agent 1",
    name="Agent1",
)

agent2 = create_default_agent(
    model=llm,
    tools=[...],
    system_prompt="You are Agent 2",
    name="Agent2",
)

# Create swarm
swarm = create_langchain_swarm(
    agents=[agent1, agent2],
    default_agent_name="Agent1",
)
```

### Using the Swarm

#### Async Invocation (Recommended)

```python
import asyncio

async def main():
    result = await swarm.invoke_async("Your query here")
    print(result)

asyncio.run(main())
```

#### Synchronous Invocation

```python
result = swarm.invoke("Your query here")
print(result)
```

## API Reference

### LangGraphSwarmAdapter

Main class for swarm orchestration.

#### Constructor

```python
LangGraphSwarmAdapter(
    agents: List[Any],
    default_agent_name: Optional[str] = None,
    **kwargs
)
```

**Parameters:**
- `agents`: List of LangChain agents
- `default_agent_name`: Name of the agent to start with (defaults to first agent)
- `**kwargs`: Additional arguments for future compatibility

#### Methods

##### `invoke_async(query: str, **kwargs) -> dict`

Asynchronously invoke the swarm.

**Parameters:**
- `query`: User query to process
- `**kwargs`: Additional arguments (e.g., `config`)

**Returns:** Dictionary with results

##### `invoke(query: str, **kwargs) -> dict`

Synchronously invoke the swarm (uses asyncio.run internally).

**Parameters:**
- `query`: User query to process
- `**kwargs`: Additional arguments

**Returns:** Dictionary with results

#### Properties

- `agents`: List of agents in the swarm
- `default_agent_name`: Name of the default agent
- `workflow`: The underlying LangGraph workflow
- `app`: The compiled LangGraph application

### Factory Function

#### `create_langchain_swarm(agents, default_agent_name=None, **kwargs)`

Creates a LangGraphSwarmAdapter instance.

**Parameters:**
- `agents`: List of agents
- `default_agent_name`: Default agent name
- `**kwargs`: Additional arguments

**Returns:** LangGraphSwarmAdapter instance

## Creating Specialized Agents

Use `create_default_agent` to create agents for the swarm:

```python
from fivcplayground.agents import create_default_agent

agent = create_default_agent(
    model=llm,
    tools=[tool1, tool2],
    system_prompt="Your system prompt here",
    name="AgentName",
)
```

## Integration with TaskTeam

For automatic swarm creation from a TaskTeam, use the `create_langchain_swarm` adapter:

```python
from fivcplayground.adapters import create_langchain_swarm
from fivcplayground.tasks.types import TaskTeam
from fivcplayground.tools import ToolsRetriever

team = TaskTeam(specialists=[...])
retriever = ToolsRetriever()

swarm = create_langchain_swarm(
    agents=[...],  # Create agents from team specialists
)
```

## Best Practices

1. **Clear System Prompts**: Define clear roles and responsibilities for each agent
2. **Tool Organization**: Assign relevant tools to each agent
3. **Error Handling**: Always wrap swarm calls in try-except blocks
4. **Async Preferred**: Use `invoke_async` for better performance
5. **Agent Naming**: Use descriptive names for agents (used in handoffs)

## Troubleshooting

### Issue: "At least one agent is required"

**Solution:** Ensure you're passing a non-empty list of agents to the swarm.

### Issue: Agent not responding

**Solution:** Check that:
- The LLM is properly configured
- Tools are correctly bound to agents
- System prompts are clear and specific

### Issue: Handoffs not working

**Solution:** Ensure agent names are unique and referenced correctly in handoff tools.

## Examples

For complete working examples, refer to the LangChain documentation and the `create_langchain_swarm` adapter implementation.

## Migration from Strands Swarm

The LangGraphSwarmAdapter maintains API compatibility with Strands Swarm:

```python
# Old Strands code
from strands.multiagent import Swarm
swarm = Swarm(agents=[...])

# New LangGraph code (same API)
from fivcplayground.adapters import create_langchain_swarm
swarm = create_langchain_swarm(agents=[...])
```

## Performance Considerations

- **Initialization**: Swarm creation is fast (~100ms)
- **Invocation**: First invocation may be slower due to LLM initialization
- **Concurrency**: Use async for better concurrency handling
- **Memory**: Each agent maintains its own state

## Advanced Configuration

### Custom Checkpointer

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
app = swarm.workflow.compile(checkpointer=checkpointer)
```

### Custom Configuration

```python
config = {
    "configurable": {
        "thread_id": "unique_thread_id",
    }
}
result = await swarm.invoke_async(query, config=config)
```

## Support

For issues or questions:
1. Check the examples in `examples/swarm_example.py`
2. Review test cases in `tests/test_langgraph_swarm_adapter.py`
3. Consult LangGraph documentation: https://langchain-ai.github.io/langgraph/

