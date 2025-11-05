"""
Agent Example - Companion Agent Usage

This example demonstrates how to use FivcAdvisor agents with LangChain.
It shows:
1. Creating a companion agent
2. Invoking the agent with queries
3. Handling agent responses
"""

import asyncio
import dotenv
import nest_asyncio

from fivcadvisor import agents

dotenv.load_dotenv()
nest_asyncio.apply()


async def main():
    """
    Run agent example demonstrating companion agent usage.
    """

    print("FivcAdvisor - Companion Agent Example")
    print("\n" + "=" * 50)

    # Create a companion agent
    from fivcadvisor.agents.types import AgentsMonitor
    agent_monitor = AgentsMonitor()
    agent = agents.create_companion_agent(
        callback_handler=agent_monitor)
    print(f"Agent ID: {agent.id}")
    print(f"Agent Name: {agent.name}")
    print()

    # Example 1: Synchronous invocation
    print("Example 1: Synchronous Invocation")
    print("-" * 50)
    query = "What time is it now?"
    print(f"Query: {query}")
    result = agent.run(query=query)
    print(f"Result: {result}")
    print()

    # Example 2: Asynchronous invocation
    print("Example 2: Asynchronous Invocation")
    print("-" * 50)
    query = "Tell me a fun fact about AI"
    print(f"Query: {query}")
    result = await agent.run_async(query=query)
    print(f"Result: {result}")
    print()

    # Example 3: Multiple queries
    print("Example 3: Multiple Queries")
    print("-" * 50)
    queries = [
        "What is machine learning?",
        "Explain neural networks",
        "What is deep learning?",
    ]

    for query in queries:
        print(f"Query: {query}")
        result = agent(query=query)
        print(f"Result: {result}\n")


if __name__ == '__main__':
    asyncio.run(main())
