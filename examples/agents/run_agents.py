"""
Agent Example - Companion Agent Usage

This example demonstrates how to use FivcPlayground agents with LangChain.
It shows:
1. Creating a companion agent
2. Invoking the agent with queries
3. Handling agent responses
"""

import asyncio
import dotenv
import nest_asyncio

from fivcplayground import agents

dotenv.load_dotenv()
nest_asyncio.apply()


async def main():
    """
    Run agent example demonstrating companion agent usage.
    """

    print("FivcPlayground - Companion Agent Example")
    print("\n" + "=" * 50)

    # Create a companion agent
    from fivcplayground import tools
    from fivcplayground.backends.strands.tools import StrandsToolBackend

    agent = await agents.create_agent_async(agent_config_id="companion")
    tool_retriever = await tools.create_tool_retriever_async(
        tool_backend=StrandsToolBackend()
    )

    print(f"Agent ID: {agent.id}")
    print(f"Agent Name: {agent.name}")
    print()

    # Example 1: Asynchronous invocation
    print("Example 1: Asynchronous Invocation")
    print("-" * 50)
    query = "What time is it now?"
    print(f"Query: {query}")
    result = await agent.run_async(
        query=query,
        tool_retriever=tool_retriever,
    )
    print(f"Result: {result}")
    print()

    # Example 2: Another asynchronous invocation
    print("Example 2: Another Asynchronous Invocation")
    print("-" * 50)
    query = "Tell me a fun fact about AI"
    print(f"Query: {query}")
    result = await agent.run_async(
        query=query,
        tool_retriever=tool_retriever,
    )
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
        result = await agent.run_async(
            query=query,
            tool_retriever=tool_retriever,
        )
        print(f"Result: {result}\n")


if __name__ == '__main__':
    asyncio.run(main())
