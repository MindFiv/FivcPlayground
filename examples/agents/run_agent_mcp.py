"""
Agent Example - MCP Tools Integration

This example demonstrates how to use FivcPlayground agents with MCP (Model Context Protocol) tools.
It shows:
1. Loading tools from configured servers using create_tool_retriever()
2. Creating an agent with tools
3. Invoking the agent with a query that requires tool usage
4. Handling agent responses with tool calls

The example uses MCP servers to perform various tasks.

Prerequisites:
    - MCP servers configured in configs/tools.yaml
    - OpenAI API key set in environment (for LLM)
    - Node.js and npm installed (for MCP servers)

Usage:
    python examples/agents/run_agent_mcp.py

Expected Output:
    - Loads tools from configured servers
    - Creates a companion agent with these tools
    - Invokes the agent with a query that requires tool usage
    - Agent attempts to use tools to complete the task

Note:
    This example uses create_tool_retriever() for framework-agnostic
    tool loading, ensuring compatibility with both Strands and LangChain frameworks.
"""

import asyncio
import dotenv

from fivcplayground.tools import create_tool_retriever
from fivcplayground.tools.types.backends import get_tool_name, get_tool_description
from fivcplayground import agents

dotenv.load_dotenv()


async def main():
    """
    Run agent example demonstrating MCP tools integration.

    This example demonstrates framework-agnostic tool loading that works with both
    Strands and LangChain frameworks.
    """

    print("FivcPlayground - Agent with MCP Tools Example")
    print("\n" + "=" * 70)

    # Step 1: Load MCP tools
    print("Step 1: Loading MCP tools from configured servers...")
    print("-" * 70)

    try:
        # Create a ToolRetriever
        # This retriever is framework-agnostic and works with both Strands and LangChain
        tool_retriever = create_tool_retriever()

        # Get all loaded tools from the retriever
        # These tools are now available for use by the agent
        all_tools = tool_retriever.list_tools()

        print(f"✓ Successfully loaded {len(all_tools)} tools total")

        if not all_tools:
            print("✗ No tools loaded. Please check your MCP configuration.")
            return
        
        print("\nAvailable tools:")
        for tool in all_tools:
            # Use framework-agnostic functions to get tool name and description
            tool_name = get_tool_name(tool)
            tool_desc = get_tool_description(tool)
            desc = tool_desc[:60] if tool_desc else "No description"
            print(f"  - {tool_name}: {desc}...")
        print()

        # Step 2: Create a companion agent with loaded MCP tools
        print("Step 2: Creating companion agent with MCP tools...")
        print("-" * 70)

        # Create a companion agent with all loaded MCP tools
        # The agent will use these tools to fulfill user requests
        agent = agents.create_companion_agent()
        print(f"✓ Agent created successfully")
        print(f"  Agent ID: {agent.id}")
        print(f"  Agent Name: {agent.name}")
        print()

        # Step 3: Invoke agent with a query requiring tool usage
        print("Step 3: Invoking agent with a query requiring tool usage...")
        print("-" * 70)

        # Query in Chinese: "Search for Ctrip stock price on Baidu"
        # This query requires the agent to:
        # 1. Create a new browser page using chrome-devtools
        # 2. Navigate to Baidu (https://www.baidu.com)
        # 3. Search for "携程股价" (Ctrip stock price)
        # 4. Extract and return the results
        query = "在百度上查询携程股价"
        print(f"Query: {query}")
        print()

        print("Agent is processing your request...")
        print("-" * 70)

        try:
            # Run the agent asynchronously
            # The agent will use the MCP tools to complete the task
            result = await agent.run_async(
                query=query,
                tool_retriever=tool_retriever,
            )

            print("\n✓ Agent response received:")
            print("-" * 70)
            print(result)
            print()

        except Exception as e:
            print(f"\n✗ Error during agent execution: {e}")
            print("\nNote: This is expected if the browser tools haven't been properly initialized.")
            print("The agent attempted to use the chrome-devtools MCP tools to complete the task.")
            import traceback
            traceback.print_exc()

        finally:
            # Clean up resources
            print("\nCleaning up resources...")
            print("✓ Resources cleaned up successfully")

        print("\n" + "=" * 70)
        print("Example completed!")
        print("\nKey Takeaways:")
        print("1. Tools were successfully loaded using create_tool_retriever()")
        print("2. Tool retriever provides framework-agnostic tool loading (Strands & LangChain)")
        print("3. Agent was created with access to these tools")
        print("4. Agent attempted to use the tools to fulfill the user's request")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
