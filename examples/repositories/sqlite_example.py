"""
Example usage of SqliteAgentRunRepository.

This example demonstrates how to use the SQLite-based repository to store
and retrieve agent runtime data, including agent metadata, execution runtimes,
and tool calls.

The SQLite repository provides:
    - Persistent storage in a relational database
    - Efficient querying and filtering
    - Referential integrity with foreign keys
    - Cascading deletes for data consistency
    - JSON storage for complex data types
"""

from datetime import datetime
from fivcplayground.agents.types import (
    AgentRunSession,
    AgentRun,
    AgentRunToolCall,
    AgentRunStatus,
    AgentRunContent,
)
from fivcplayground.agents.types.repositories import SqliteAgentRunRepository


def example_1_basic_agent_storage():
    """Example 1: Store and retrieve agent metadata."""
    print("\n" + "="*60)
    print("Example 1: Basic Agent Storage")
    print("="*60)
    
    # Create repository
    repo = SqliteAgentRunRepository(db_path="./examples_agents.db")
    
    # Create agent metadata
    agent = AgentRunSession(
        agent_id="customer-support-agent",
        description="Handles customer inquiries and support requests",
    )

    # Store agent
    repo.update_agent(agent)
    print(f"✓ Stored agent: {agent.agent_id}")

    # Retrieve agent
    retrieved = repo.get_agent("customer-support-agent")
    print(f"✓ Retrieved agent: {retrieved.agent_id}")
    print(f"  System prompt: {retrieved.system_prompt}")
    
    repo.close()


def example_2_agent_runtime_execution():
    """Example 2: Track agent runtime execution."""
    print("\n" + "="*60)
    print("Example 2: Agent Runtime Execution")
    print("="*60)
    
    repo = SqliteAgentRunRepository(db_path="./examples_agents.db")
    
    # Create agent
    agent = AgentRunSession(
        agent_id="math-agent",
        description="You are a math expert.",
    )
    repo.update_agent(agent)

    # Create runtime for agent execution
    runtime = AgentRun(
        agent_id="math-agent",
        status=AgentRunStatus.EXECUTING,
        query=AgentRunContent(text="What is 2 + 2?"),
        started_at=datetime.now(),
    )
    
    # Store runtime
    repo.update_agent_run("math-agent", runtime)
    print(f"✓ Created runtime: {runtime.id}")
    print(f"  Status: {runtime.status}")
    print(f"  Query: {runtime.query.text}")
    
    # Simulate execution completion
    runtime.status = AgentRunStatus.COMPLETED
    runtime.completed_at = datetime.now()
    runtime.reply = AgentRunContent(text="2 + 2 = 4")
    
    # Update runtime
    repo.update_agent_run("math-agent", runtime)
    print(f"✓ Updated runtime status: {runtime.status}")
    print(f"  Reply: {runtime.reply.text}")
    
    repo.close()


def example_3_tool_calls_tracking():
    """Example 3: Track tool calls within a runtime."""
    print("\n" + "="*60)
    print("Example 3: Tool Calls Tracking")
    print("="*60)

    repo = SqliteAgentRunRepository(db_path="./examples_agents.db")

    # Create agent and runtime
    agent = AgentRunSession(agent_id="calculator-agent")
    repo.update_agent_run_session(agent)

    runtime = AgentRun(
        agent_id="calculator-agent",
        query=AgentRunContent(text="Calculate 10 * 5"),
    )
    repo.update_agent_run("calculator-agent", runtime)

    # Create tool call
    tool_call = AgentRunToolCall(
        id="call-001",
        tool_name="calculator",
        tool_input={"expression": "10 * 5"},
        status="pending",
        started_at=datetime.now(),
    )

    # Add tool call to runtime (embedded)
    runtime.tool_calls["call-001"] = tool_call
    print(f"✓ Created tool call: {tool_call.id}")
    print(f"  Tool: {tool_call.tool_name}")
    print(f"  Input: {tool_call.tool_input}")

    # Simulate tool execution
    tool_call.status = "success"
    tool_call.tool_result = 50
    tool_call.completed_at = datetime.now()

    # Update runtime with modified tool call
    runtime.tool_calls["call-001"] = tool_call
    repo.update_agent_run("calculator-agent", runtime)
    print(f"✓ Updated tool call status: {tool_call.status}")
    print(f"  Result: {tool_call.tool_result}")

    repo.close()


def example_4_list_and_query():
    """Example 4: List and query stored data."""
    print("\n" + "="*60)
    print("Example 4: List and Query")
    print("="*60)

    repo = SqliteAgentRunRepository(db_path="./examples_agents.db")

    # List all agents
    agents = repo.list_agent_run_sessions()
    print(f"✓ Total agents: {len(agents)}")
    for agent in agents:
        print(f"  - {agent.agent_id}")

    # List runtimes for an agent
    if agents:
        agent_id = agents[0].agent_id
        runtimes = repo.list_agent_runs(agent_id)
        print(f"\n✓ Runtimes for {agent_id}: {len(runtimes)}")
        for runtime in runtimes:
            print(f"  - {runtime.id}: {runtime.status}")

            # List tool calls from runtime (embedded)
            tool_calls = list(runtime.tool_calls.values())
            print(f"    Tool calls: {len(tool_calls)}")
            for tool_call in tool_calls:
                print(f"      - {tool_call.id}: {tool_call.tool_name}")
    
    repo.close()


def example_5_cascading_deletes():
    """Example 5: Demonstrate cascading deletes."""
    print("\n" + "="*60)
    print("Example 5: Cascading Deletes")
    print("="*60)
    
    repo = SqliteAgentRunRepository(db_path="./examples_agents.db")
    
    # Create test data
    agent = AgentRunSession(agent_id="temp-agent")
    repo.update_agent_run_session(agent)

    runtime = AgentRun(agent_id="temp-agent")

    tool_call = AgentRunToolCall(
        id="temp-call",
        tool_name="test_tool",
    )
    runtime.tool_calls["temp-call"] = tool_call

    repo.update_agent_run("temp-agent", runtime)

    print(f"✓ Created test data")
    print(f"  Agents: {len(repo.list_agent_run_sessions())}")
    print(f"  Runtimes: {len(repo.list_agent_runs('temp-agent'))}")
    print(f"  Tool calls: {len(runtime.tool_calls)}")

    # Delete agent (cascades to runtimes and tool calls)
    repo.delete_agent_run_session("temp-agent")
    print(f"\n✓ Deleted agent 'temp-agent'")
    print(f"  Agents: {len(repo.list_agent_run_sessions())}")
    print(f"  Runtimes: {len(repo.list_agent_runs('temp-agent'))}")
    print(f"  Tool calls: 0")
    
    repo.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SqliteAgentRunRepository Examples")
    print("="*60)
    
    example_1_basic_agent_storage()
    example_2_agent_runtime_execution()
    example_3_tool_calls_tracking()
    example_4_list_and_query()
    example_5_cascading_deletes()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")

