# LangChain Advanced Examples

## 🚀 Advanced Usage Patterns

This guide provides advanced examples for using FivcPlayground with LangChain.

---

## 1. Custom Agent with Event Handling

### Example: Agent with Event Logging

```python
import asyncio
from fivcplayground.agents import create_companion_agent

async def main():
    agent = create_companion_agent()
    
    # Subscribe to events
    def on_before_invocation(event):
        print(f"🚀 Starting invocation with query: {event.get('query')}")
    
    def on_after_invocation(event):
        print(f"✅ Invocation complete: {event.get('result')}")
    
    def on_error(event):
        print(f"❌ Error: {event.get('error')}")
    
    agent.event_bus.subscribe("BEFORE_INVOCATION", on_before_invocation)
    agent.event_bus.subscribe("AFTER_INVOCATION", on_after_invocation)
    agent.event_bus.subscribe("ERROR", on_error)
    
    # Invoke agent
    result = await agent.invoke_async("What is machine learning?")
    print(f"Result: {result}")

asyncio.run(main())
```

---

## 2. Multi-Agent Swarm with Task Routing

### Example: Specialized Agent Swarm

```python
from fivcplayground.agents import create_generic_agent_swarm
from fivcplayground.tasks.types import TaskTeam, TaskSpecialist
from fivcplayground.tools.types import ToolsRetriever

# Create specialist agents
specialists = [
    TaskSpecialist(
        name="DataAnalyst",
        description="Analyzes data and provides insights",
        agent_type="research"
    ),
    TaskSpecialist(
        name="Planner",
        description="Plans projects and workflows",
        agent_type="planning"
    ),
    TaskSpecialist(
        name="Consultant",
        description="Provides expert advice",
        agent_type="consultant"
    ),
]

team = TaskTeam(specialists=specialists)

# Create swarm using the LangChain adapter
async def main():
    from fivcplayground.adapters import create_langchain_swarm

    # Create agents from team specialists
    agents = [create_default_agent(name=s.name, system_prompt=s.backstory)
              for s in team.specialists]

    swarm = create_langchain_swarm(agents=agents)

    # Complex query that routes to appropriate agents
    result = await swarm.invoke_async(
        "Analyze our sales data and plan next quarter strategy"
    )
    print(result)

asyncio.run(main())
```

---

## 3. Custom Tools Integration

### Example: Adding Custom Tools

```python
from fivcplayground.agents import create_tooling_agent
from fivcplayground.tools.types import AgentTool

# Define custom tools
def calculate_sum(numbers: str) -> str:
    """Calculate sum of numbers"""
    nums = [float(x) for x in numbers.split(",")]
    return str(sum(nums))

def get_weather(city: str) -> str:
    """Get weather for a city"""
    # In real app, call weather API
    return f"Weather in {city}: Sunny, 72°F"

# Create tools
tools = [
    AgentTool(
        tool_name="calculator",
        tool_spec={
            "description": "Calculates sum of comma-separated numbers",
            "parameters": {
                "type": "object",
                "properties": {
                    "numbers": {"type": "string", "description": "Comma-separated numbers"}
                }
            }
        },
        func=calculate_sum
    ),
    AgentTool(
        tool_name="weather",
        tool_spec={
            "description": "Gets weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                }
            }
        },
        func=get_weather
    ),
]

# Use with agent
async def main():
    agent = create_tooling_agent()
    result = await agent.invoke_with_tools(
        "What's the sum of 10, 20, 30 and weather in NYC?",
        tools
    )
    print(result)

asyncio.run(main())
```

---

## 4. Streaming Responses

### Example: Streaming Agent Output

```python
from fivcplayground.agents import create_companion_agent

async def main():
    agent = create_companion_agent()
    
    # Subscribe to streaming events
    def on_token(event):
        token = event.get('token', '')
        print(token, end='', flush=True)
    
    agent.event_bus.subscribe("TOKEN_GENERATED", on_token)
    
    # Invoke with streaming
    result = await agent.invoke_async("Explain quantum computing")
    print()  # New line after streaming

asyncio.run(main())
```

---

## 5. Error Handling and Retry Logic

### Example: Robust Agent Invocation

```python
import asyncio
from fivcplayground.agents import create_companion_agent

async def invoke_with_retry(agent, query, max_retries=3):
    """Invoke agent with retry logic"""
    for attempt in range(max_retries):
        try:
            result = await agent.invoke_async(query)
            return result
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

async def main():
    agent = create_companion_agent()
    
    try:
        result = await invoke_with_retry(
            agent,
            "What is artificial intelligence?"
        )
        print(f"Success: {result}")
    except Exception as e:
        print(f"Failed after retries: {e}")

asyncio.run(main())
```

---

## 6. Batch Processing

### Example: Processing Multiple Queries

```python
import asyncio
from fivcplayground.agents import create_companion_agent

async def process_batch(queries):
    """Process multiple queries concurrently"""
    agent = create_companion_agent()
    
    tasks = [
        agent.invoke_async(query)
        for query in queries
    ]
    
    results = await asyncio.gather(*tasks)
    return results

async def main():
    queries = [
        "What is machine learning?",
        "Explain deep learning",
        "What is NLP?",
    ]
    
    results = await process_batch(queries)
    
    for query, result in zip(queries, results):
        print(f"Q: {query}")
        print(f"A: {result}\n")

asyncio.run(main())
```

---

## 7. Agent Chaining

### Example: Sequential Agent Calls

```python
import asyncio
from fivcplayground.agents import (
    create_research_agent,
    create_consultant_agent,
    create_planning_agent
)

async def main():
    # Step 1: Research
    research_agent = create_research_agent()
    research_result = await research_agent.invoke_async(
        "Research the latest AI trends"
    )
    print(f"Research: {research_result}\n")
    
    # Step 2: Consult
    consultant_agent = create_consultant_agent()
    consultant_result = await consultant_agent.invoke_async(
        f"Based on this research: {research_result}, what should we do?"
    )
    print(f"Consultation: {consultant_result}\n")
    
    # Step 3: Plan
    planning_agent = create_planning_agent()
    plan_result = await planning_agent.invoke_async(
        f"Create a plan based on: {consultant_result}"
    )
    print(f"Plan: {plan_result}")

asyncio.run(main())
```

---

## 8. Performance Monitoring

### Example: Tracking Agent Performance

```python
import time
import asyncio
from fivcplayground.agents import create_companion_agent

async def main():
    agent = create_companion_agent()
    
    queries = [
        "What is AI?",
        "Explain machine learning",
        "What is deep learning?",
    ]
    
    times = []
    
    for query in queries:
        start = time.time()
        result = await agent.invoke_async(query)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"Query: {query}")
        print(f"Time: {elapsed:.3f}s\n")
    
    avg_time = sum(times) / len(times)
    print(f"Average time: {avg_time:.3f}s")
    print(f"Min time: {min(times):.3f}s")
    print(f"Max time: {max(times):.3f}s")

asyncio.run(main())
```

---

## 9. Context Management

### Example: Maintaining Conversation Context

```python
import asyncio
from fivcplayground.agents import create_companion_agent

class ConversationManager:
    def __init__(self):
        self.agent = create_companion_agent()
        self.history = []
    
    async def chat(self, message):
        """Send message and maintain context"""
        # Add to history
        self.history.append({"role": "user", "content": message})
        
        # Create context from history
        context = "\n".join([
            f"{h['role']}: {h['content']}"
            for h in self.history[-5:]  # Last 5 messages
        ])
        
        # Invoke with context
        full_query = f"Context:\n{context}\n\nRespond to the latest message."
        result = await self.agent.invoke_async(full_query)
        
        # Add response to history
        self.history.append({"role": "assistant", "content": result})
        
        return result

async def main():
    manager = ConversationManager()
    
    response1 = await manager.chat("What is AI?")
    print(f"Assistant: {response1}\n")
    
    response2 = await manager.chat("Can you explain it more simply?")
    print(f"Assistant: {response2}\n")
    
    response3 = await manager.chat("What are some applications?")
    print(f"Assistant: {response3}")

asyncio.run(main())
```

---

## 10. Custom Model Configuration

### Example: Using Different Models

```python
from fivcplayground.adapters.models import create_openai_model, create_ollama_model
from fivcplayground.adapters.agents import LangChainAgentAdapter

# Create with OpenAI
openai_model = create_openai_model(
    api_key="sk-...",
    model="gpt-4"
)

# Create with Ollama
ollama_model = create_ollama_model(
    base_url="http://localhost:11434",
    model="llama2"
)

# Create agents with different models
async def main():
    openai_agent = LangChainAgentAdapter(
        model=openai_model,
        tools=[],
        name="OpenAIAgent"
    )
    
    ollama_agent = LangChainAgentAdapter(
        model=ollama_model,
        tools=[],
        name="OllamaAgent"
    )
    
    # Compare responses
    query = "What is machine learning?"
    
    openai_result = await openai_agent.invoke_async(query)
    print(f"OpenAI: {openai_result}\n")
    
    ollama_result = await ollama_agent.invoke_async(query)
    print(f"Ollama: {ollama_result}")

asyncio.run(main())
```

---

## 📚 Related Documentation

- [LangChain Migration Guide](LANGCHAIN_MIGRATION_GUIDE.md)
- [API Reference](LANGCHAIN_API_REFERENCE.md)
- [Test Examples](../tests/test_langchain_integration.py)

---

**Last Updated**: 2025-10-24
**Status**: ✅ Complete
**Examples**: 10 advanced patterns

