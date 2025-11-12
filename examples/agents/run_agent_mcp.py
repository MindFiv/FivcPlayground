"""
Agent Example - MCP Tools Integration

This example demonstrates how to use FivcAdvisor agents with MCP (Model Context Protocol) tools.
It shows:
1. Loading MCP tools (chrome-devtools) from configured servers using ToolsLoader
2. Creating an agent with MCP tools
3. Invoking the agent with a query that requires tool usage
4. Handling agent responses with tool calls

The example uses chrome-devtools MCP server to perform web searches and browsing tasks.

Prerequisites:
    - MCP servers configured in configs/mcp.yaml (chrome-devtools, sequential-thinking)
    - OpenAI API key set in environment (for LLM)
    - Node.js and npm installed (for MCP servers)

Usage:
    python examples/agents/run_agent_mcp.py

Expected Output:
    - Loads 28 tools from configured MCP servers
    - Creates a companion agent with these tools
    - Invokes the agent with a Chinese query: "在百度上查询携程股价" (Search for Ctrip stock price on Baidu)
    - Agent attempts to use chrome-devtools to navigate and search

Note:
    This example uses ToolsLoader for framework-agnostic tool loading, ensuring compatibility
    with both Strands and LangChain frameworks.
"""

import asyncio
import dotenv

from fivcplayground.tools.types.loaders import ToolsLoader
from fivcplayground.tools.types.retrievers import ToolsRetriever
from fivcplayground.tools.types.backends import get_tool_name, get_tool_description
from fivcplayground import agents
from fivcplayground.agents.types import AgentsMonitor

dotenv.load_dotenv()


async def main():
    """
    Run agent example demonstrating MCP tools integration using ToolsLoader.

    This example demonstrates framework-agnostic tool loading that works with both
    Strands and LangChain frameworks.
    """

    print("FivcAdvisor - Agent with MCP Tools Example")
    print("\n" + "=" * 70)

    # Step 1: Load MCP tools using ToolsLoader
    print("Step 1: Loading MCP tools from configured servers...")
    print("-" * 70)

    try:
        # Create a ToolsRetriever to manage tools
        # This retriever is framework-agnostic and works with both Strands and LangChain
        tools_retriever = ToolsRetriever()

        # Create a ToolsLoader with the retriever
        # ToolsLoader handles loading tools from MCP servers configured in mcp.yaml
        loader = ToolsLoader(
            tools_retriever=tools_retriever,
            config_file="configs/mcp.yaml"
        )

        # Load all configured MCP tools asynchronously
        # This loads tools from all servers defined in configs/mcp.yaml
        await loader.load_async()

        # Get all loaded tools from the retriever
        # These tools are now available for use by the agent
        all_tools = tools_retriever.get_all()

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

        # Create an AgentsMonitor to track agent execution
        agent_monitor = AgentsMonitor()

        # Create a companion agent with all loaded MCP tools
        # The agent will use these tools to fulfill user requests
        agent = agents.create_companion_agent(
            callback_handler=agent_monitor,
            tools=all_tools  # Pass all loaded MCP tools to the agent
        )
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
            result = await agent.run_async(query=query)

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
            await loader.cleanup_async()
            print("✓ Resources cleaned up successfully")

        print("\n" + "=" * 70)
        print("Example completed!")
        print("\nKey Takeaways:")
        print("1. MCP tools were successfully loaded using ToolsLoader")
        print("2. ToolsLoader provides framework-agnostic tool loading (Strands & LangChain)")
        print("3. Agent was created with access to these tools")
        print("4. Agent attempted to use the tools to fulfill the user's request")
        print("5. Tool execution can be monitored and debugged using AgentsMonitor")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
