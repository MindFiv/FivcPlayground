#!/usr/bin/env python3
"""
Example demonstrating multi-space (multi-tenant) architecture for ToolRetriever.

This example shows how to use embedding spaces to isolate tools for different:
- Users (user_alice, user_bob)
- Projects (project_website, project_mobile_app)
- Environments (env_dev, env_staging, env_prod)
- Teams (team_engineering, team_marketing)
- Experiments (experiment_ab_test_1)

Each space has its own isolated collection in ChromaDB, ensuring complete data isolation.
"""

import asyncio
from fivcplayground.tools import create_tool_retriever_async
from fivcplayground.backends.strands.tools import StrandsToolBackend


async def example_user_specific_tools():
    """Example: Create user-specific tool retrievers."""
    print("\n=== User-Specific Tools ===")

    # Create tool retriever for Alice
    alice_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        space_id="user_alice",
        load_builtin_tools=False,
    )
    print(f"Created retriever for Alice: space_id={alice_retriever.space_id}")

    # Create tool retriever for Bob
    bob_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        space_id="user_bob",
        load_builtin_tools=False,
    )
    print(f"Created retriever for Bob: space_id={bob_retriever.space_id}")

    # Alice and Bob have completely isolated tool collections
    # Tools added to alice_retriever won't be visible to bob_retriever


async def example_project_specific_tools():
    """Example: Create project-specific tool retrievers."""
    print("\n=== Project-Specific Tools ===")

    # Create tool retriever for website project
    website_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        space_id="project_website",
        load_builtin_tools=True,  # Load default tools for this project
    )
    print(f"Created retriever for website project: space_id={website_retriever.space_id}")

    # Create tool retriever for mobile app project
    mobile_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        space_id="project_mobile_app",
        load_builtin_tools=False,
    )
    print(f"Created retriever for mobile app: space_id={mobile_retriever.space_id}")


async def example_environment_specific_tools():
    """Example: Create environment-specific tool retrievers."""
    print("\n=== Environment-Specific Tools ===")

    # Create tool retrievers for different environments
    dev_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        space_id="env_dev",
        load_builtin_tools=True,
    )
    print(f"Created retriever for dev environment: space_id={dev_retriever.space_id}")

    staging_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        space_id="env_staging",
        load_builtin_tools=True,
    )
    print(f"Created retriever for staging: space_id={staging_retriever.space_id}")

    prod_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        space_id="env_prod",
        load_builtin_tools=True,
    )
    print(f"Created retriever for production: space_id={prod_retriever.space_id}")


async def example_default_space():
    """Example: Use the default space."""
    print("\n=== Default Space ===")

    # Create tool retriever without space_id (uses default space)
    default_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        space_id=None,  # or simply omit the parameter
        load_builtin_tools=True,
    )
    print(f"Created retriever for default space: space_id={default_retriever.space_id}")

    # Create another retriever with explicit backend
    another_retriever = await create_tool_retriever_async(
        tool_backend=StrandsToolBackend(),
        load_builtin_tools=True,
    )
    print(f"Another retriever (no space_id): space_id={another_retriever.space_id}")


async def main():
    """Run all examples."""
    print("Multi-Space Architecture Examples")
    print("=" * 50)

    await example_user_specific_tools()
    await example_project_specific_tools()
    await example_environment_specific_tools()
    await example_default_space()

    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())

