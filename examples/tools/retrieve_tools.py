"""
Tool Retriever Example

This example demonstrates how to use the ToolRetriever to:
1. Load MCP tools from configured servers
2. Retrieve tools based on semantic search
3. Use retrieved tools with agents
"""

import asyncio
import dotenv

from fivcplayground.utils import OutputDir
from fivcplayground.tools import create_tool_retriever
from fivcplayground.tools.clock import clock
from fivcplayground.tools.calculator import calculator

dotenv.load_dotenv()


async def main():
    """
    Run the tool retriever example.
    """

    print("FivcPlayground - Tool Retriever Example")
    print("\n" + "=" * 50)

    # Use OutputDir context manager for proper directory handling
    with OutputDir():
        # Create a retriever instance with builtin and MCP tools
        # Tools are passed during initialization
        retriever = create_tool_retriever(
            load_builtin_tools=True,
            load_mcp_tools=True,
        )

        print("Tools loaded successfully!")
        print("\n" + "=" * 50)

        # Retrieve tools based on semantic search
        query = "How to become a millionaire? think step by step"
        print(f"\nQuery: {query}")
        print("\nRetrieving relevant tools...")

        result = retriever.retrieve_tools(query)

        print(f'\nFound {len(result)} relevant tools:')
        for i, tool in enumerate(result, 1):
            print('-------------------------')
            print(f"Tool {i}: {tool}")


if __name__ == '__main__':
    asyncio.run(main())
