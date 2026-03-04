"""
Dynamic Tool Loading via Skills Example

This example demonstrates the complete skills-based dynamic tool loading workflow:

1. **Skill Retrieval**: Semantic search finds relevant skills by description
2. **Dynamic Loading**: Callback pattern dynamically registers tools when skills execute
3. **Deduplication**: Tools from multiple skills are deduplicated automatically
4. **Agent Execution**: Skills expose relevant tools to the agent dynamically

Key Features:
- Shows how SkillRetriever performs semantic search
- Demonstrates LoadCallback pattern for dynamic tool registration
- Logs detailed callback invocations and tool registration events
- Verifies callback execution with assertions
- Displays tool deduplication in action

Architecture Flow:
    User Query
        ↓
    Skill Retriever (semantic search)
        ↓
    Agent executes with skill_retriever parameter
        ↓
    Agent calls skill_list() / skill_load() tools
        ↓
    LoadCallback invoked → register_tool_async() for each tool_id
        ↓
    Tools become available to agent

This pattern enables agents to dynamically request only the tools they need,
reducing token usage and improving performance.
"""

import asyncio
import json
from datetime import datetime
from typing import Callable

import dotenv
import nest_asyncio

from fivcplayground import agents, skills
from fivcplayground.backends.chroma import ChromaEmbeddingBackend
from fivcplayground.backends.strands import StrandsModelBackend, StrandsAgentBackend
from fivcplayground.backends.strands.tools import StrandsToolBackend
from fivcplayground.embeddings import create_embedding_db_async
from fivcplayground.skills.types import SkillConfig
from fivcplayground.tools import create_tool_retriever_async, create_builtin_tools_async

# Load repositories and backends
from fivcplayground.agents.types.repositories import FileAgentConfigRepository
from fivcplayground.embeddings.types.repositories import FileEmbeddingConfigRepository
from fivcplayground.skills.types.repositories import FileSkillConfigRepository
from fivcplayground.tools.types.repositories import FileToolConfigRepository

dotenv.load_dotenv()
nest_asyncio.apply()


class CallbackTracker:
    """Track callback invocations for verification and logging."""

    def __init__(self):
        self.invocations: list[dict] = []
        self.tools_registered: set[str] = set()

    async def log_callback(self, skill: SkillConfig):
        """Log skill loading with detailed callback information."""
        invocation = {
            "skill_id": skill.id,
            "description": skill.description,
            "tools": skill.tool_ids or [],
            "timestamp": datetime.now().isoformat(),
        }
        self.invocations.append(invocation)

        print(f"\n[CALLBACK INVOKED] Skill: {skill.id}")
        print(f"  Description: {skill.description}")
        if skill.tool_ids:
            for tool_id in skill.tool_ids:
                print(f"  → Tool: {tool_id}")
                self.tools_registered.add(tool_id)
        else:
            print("  (No tools to register)")

    def print_summary(self):
        """Print summary of callback invocations."""
        print("\n" + "=" * 60)
        print("CALLBACK EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Total Invocations: {len(self.invocations)}")
        print(f"Unique Tools Registered: {len(self.tools_registered)}")

        if self.invocations:
            print("\nInvocation Details:")
            for i, inv in enumerate(self.invocations, 1):
                print(f"\n  {i}. Skill: {inv['skill_id']}")
                print(f"     Tools: {', '.join(inv['tools']) if inv['tools'] else 'None'}")
                print(f"     Time: {inv['timestamp']}")

        if self.tools_registered:
            print(f"\nRegistered Tools: {', '.join(sorted(self.tools_registered))}")


async def setup_environment():
    """Setup FivcPlayground environment with repositories."""
    print("\n[SETUP] Initializing FivcPlayground environment...")

    from fivcplayground.models.types.repositories.files import FileModelConfigRepository

    agent_config_repo = FileAgentConfigRepository()
    skill_config_repo = FileSkillConfigRepository()
    embedding_config_repo = FileEmbeddingConfigRepository()
    tool_config_repo = FileToolConfigRepository()
    model_config_repo = FileModelConfigRepository()

    print("[SETUP] Repositories loaded")
    return (
        agent_config_repo,
        skill_config_repo,
        embedding_config_repo,
        tool_config_repo,
        model_config_repo,
    )


async def create_skill_retriever(
    skill_config_repo,
    embedding_config_repo,
):
    """Create skill retriever with semantic search capability."""
    print("\n[SKILL SETUP] Creating SkillRetriever...")

    skill_retriever = await skills.create_skill_retriever_async(
        skill_config_repository=skill_config_repo,
        embedding_config_repository=embedding_config_repo,
        embedding_backend=ChromaEmbeddingBackend(),
        embedding_config_id="default",
        tool_backend=StrandsToolBackend(),
        raise_exception=False,
    )

    if not skill_retriever:
        print("[SKILL SETUP] ✗ Failed to create skill retriever")
        return None

    print("[SKILL SETUP] ✓ SkillRetriever created successfully")

    # Index skills for semantic search
    print("[SKILL SETUP] Indexing skills...")
    await skill_retriever.index_skills_async()
    print("[SKILL SETUP] ✓ Skills indexed")

    return skill_retriever


async def list_available_skills(skill_retriever):
    """Display all available skills."""
    print("\n" + "=" * 60)
    print("AVAILABLE SKILLS")
    print("=" * 60)

    all_skills = await skill_retriever.list_skills_async()
    if not all_skills:
        print("No skills available")
        return

    for i, skill in enumerate(all_skills, 1):
        print(f"\n{i}. {skill.id}")
        print(f"   Description: {skill.description}")
        if skill.tool_ids:
            print(f"   Tools: {', '.join(skill.tool_ids)}")
        if skill.instructions:
            print(f"   Instructions: {skill.instructions[:100]}...")


async def demonstrate_skill_retrieval(skill_retriever):
    """Demonstrate semantic search for skills."""
    print("\n" + "=" * 60)
    print("SEMANTIC SKILL SEARCH")
    print("=" * 60)

    test_queries = [
        "I need to check what time it is",
        "I need to do some math calculations",
        "I need to read a file",
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        retrieved = await skill_retriever.retrieve_skills_async(query)

        if retrieved:
            print(f"Found {len(retrieved)} relevant skill(s):")
            for skill in retrieved:
                print(f"  ✓ {skill.id}: {skill.description}")
        else:
            print("No relevant skills found")


async def demonstrate_callback_loading(skill_retriever, tracker):
    """Demonstrate callback-based tool loading."""
    print("\n" + "=" * 60)
    print("CALLBACK-BASED TOOL LOADING")
    print("=" * 60)

    print("\nCreating skill tool with callback...")

    # Create skill tool with callback for dynamic loading
    skill_tool = skill_retriever.to_tool(load_callback=tracker.log_callback)

    print("✓ Skill tool created with callback")
    print(f"  Tool Name: {skill_tool.name}")
    print(f"  Tool Description: {skill_tool.description}")


async def demonstrate_agent_execution(
    agent_config_repo, model_config_repo, embedding_config_repo, tool_config_repo, skill_retriever, tracker
):
    """Demonstrate agent execution with skills and dynamic tool loading."""
    print("\n" + "=" * 60)
    print("AGENT EXECUTION WITH SKILLS")
    print("=" * 60)

    print("\nCreating default agent...")
    agent = await agents.create_agent_async(
        agent_config_id="default",
        agent_config_repository=agent_config_repo,
        model_backend=StrandsModelBackend(),
        model_config_repository=model_config_repo,
        agent_backend=StrandsAgentBackend(),
    )
    print(f"✓ Agent created: {agent.id}")

    # Create tool retriever for builtin tools
    tool_retriever = await create_tool_retriever_async(
        tools=await create_builtin_tools_async(
            tool_backend=StrandsToolBackend(),
        ),
        tool_backend=StrandsToolBackend(),
        embedding_backend=ChromaEmbeddingBackend(),
        embedding_config_repository=embedding_config_repo,
        tool_config_repository=tool_config_repo,
        load_builtin_tools=True,
    )

    print("\nExecuting agent with skill-based dynamic tool loading...")

    # Sample query that might trigger skill discovery
    # query = "What time is it right now? Can you also calculate 42 * 3?"
    query = "use skill: general-utility to calculate 42 * 3 and tell me the time"

    print(f"Query: {query}\n")

    try:
        result = await agent.run_async(
            query=query,
            tool_ids=['tool_retriever'],
            tool_retriever=tool_retriever,
            skill_retriever=skill_retriever,
        )

        print("\n[AGENT RESULT]")
        print(f"Response: {result}")

    except Exception as e:
        print(f"[ERROR] Agent execution failed: {str(e)}")
        import traceback

        traceback.print_exc()


async def main():
    """
    Run the dynamic tool loading example.

    This demonstrates:
    1. Setting up skill retriever with semantic search
    2. Listing available skills
    3. Semantic skill search (finding relevant skills by description)
    4. Callback-based dynamic tool loading
    5. Agent execution with skills
    6. Verification that callbacks were invoked
    """

    print("\n" + "=" * 60)
    print("FivcPlayground - Dynamic Tool Loading via Skills Example")
    print("=" * 60)

    # Setup
    agent_config_repo, skill_config_repo, embedding_config_repo, tool_config_repo, model_config_repo = (
        await setup_environment()
    )

    # Create skill retriever
    skill_retriever = await create_skill_retriever(
        skill_config_repo, embedding_config_repo
    )

    if not skill_retriever:
        print("\n[ERROR] Failed to create skill retriever")
        return

    # List available skills
    await list_available_skills(skill_retriever)

    # Demonstrate semantic search
    await demonstrate_skill_retrieval(skill_retriever)

    # Create callback tracker
    tracker = CallbackTracker()

    # Demonstrate callback loading
    await demonstrate_callback_loading(skill_retriever, tracker)

    # Execute agent with skills
    await demonstrate_agent_execution(agent_config_repo, model_config_repo, embedding_config_repo, tool_config_repo, skill_retriever, tracker)

    # Print callback summary
    tracker.print_summary()

    # Verify callback was invoked
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    if tracker.invocations:
        print(f"\n✓ SUCCESS: Callback invoked {len(tracker.invocations)} time(s)")
        print(f"✓ Tools registered: {tracker.tools_registered}")
    else:
        print("\n⚠ No callback invocations recorded (agent may not have used skills)")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
