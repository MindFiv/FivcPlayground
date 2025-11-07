"""
Example usage of SqliteAgentsRuntimeRepository.

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
from fivcadvisor.agents.types import (
    AgentsRuntimeMeta,
    AgentsRuntime,
    AgentsRuntimeToolCall,
    AgentsStatus,
    AgentsContent,
)
from fivcadvisor.agents.types.repositories import SqliteAgentsRuntimeRepository


def example_1_basic_agent_storage():
    """Example 1: Store and retrieve agent metadata."""
    print("\n" + "="*60)
    print("Example 1: Basic Agent Storage")
    print("="*60)
    
    # Create repository
    repo = SqliteAgentsRuntimeRepository(db_path="./examples_agents.db")
    
    # Create agent metadata
    agent = AgentsRuntimeMeta(
        agent_id="customer-support-agent",
        agent_name="Customer Support Agent",
        system_prompt="You are a helpful customer support assistant.",
        description="Handles customer inquiries and support requests",
    )
    
    # Store agent
    repo.update_agent(agent)
    print(f"✓ Stored agent: {agent.agent_name}")
    
    # Retrieve agent
    retrieved = repo.get_agent("customer-support-agent")
    print(f"✓ Retrieved agent: {retrieved.agent_name}")
    print(f"  System prompt: {retrieved.system_prompt}")
    
    repo.close()


def example_2_agent_runtime_execution():
    """Example 2: Track agent runtime execution."""
    print("\n" + "="*60)
    print("Example 2: Agent Runtime Execution")
    print("="*60)
    
    repo = SqliteAgentsRuntimeRepository(db_path="./examples_agents.db")
    
    # Create agent
    agent = AgentsRuntimeMeta(
        agent_id="math-agent",
        agent_name="Math Agent",
        system_prompt="You are a math expert.",
    )
    repo.update_agent(agent)
    
    # Create runtime for agent execution
    runtime = AgentsRuntime(
        agent_id="math-agent",
        agent_name="Math Agent",
        status=AgentsStatus.EXECUTING,
        query=AgentsContent(text="What is 2 + 2?"),
        started_at=datetime.now(),
    )
    
    # Store runtime
    repo.update_agent_runtime("math-agent", runtime)
    print(f"✓ Created runtime: {runtime.agent_run_id}")
    print(f"  Status: {runtime.status}")
    print(f"  Query: {runtime.query.text}")
    
    # Simulate execution completion
    runtime.status = AgentsStatus.COMPLETED
    runtime.completed_at = datetime.now()
    runtime.reply = AgentsContent(text="2 + 2 = 4")
    
    # Update runtime
    repo.update_agent_runtime("math-agent", runtime)
    print(f"✓ Updated runtime status: {runtime.status}")
    print(f"  Reply: {runtime.reply.text}")
    
    repo.close()


def example_3_tool_calls_tracking():
    """Example 3: Track tool calls within a runtime."""
    print("\n" + "="*60)
    print("Example 3: Tool Calls Tracking")
    print("="*60)
    
    repo = SqliteAgentsRuntimeRepository(db_path="./examples_agents.db")
    
    # Create agent and runtime
    agent = AgentsRuntimeMeta(agent_id="calculator-agent")
    repo.update_agent(agent)
    
    runtime = AgentsRuntime(
        agent_id="calculator-agent",
        query=AgentsContent(text="Calculate 10 * 5"),
    )
    repo.update_agent_runtime("calculator-agent", runtime)
    
    # Create tool call
    tool_call = AgentsRuntimeToolCall(
        tool_use_id="call-001",
        tool_name="calculator",
        tool_input={"expression": "10 * 5"},
        status="pending",
        started_at=datetime.now(),
    )
    
    # Store tool call
    repo.update_agent_runtime_tool_call(
        "calculator-agent", runtime.agent_run_id, tool_call
    )
    print(f"✓ Created tool call: {tool_call.tool_use_id}")
    print(f"  Tool: {tool_call.tool_name}")
    print(f"  Input: {tool_call.tool_input}")
    
    # Simulate tool execution
    tool_call.status = "success"
    tool_call.tool_result = 50
    tool_call.completed_at = datetime.now()
    
    # Update tool call
    repo.update_agent_runtime_tool_call(
        "calculator-agent", runtime.agent_run_id, tool_call
    )
    print(f"✓ Updated tool call status: {tool_call.status}")
    print(f"  Result: {tool_call.tool_result}")
    
    repo.close()


def example_4_list_and_query():
    """Example 4: List and query stored data."""
    print("\n" + "="*60)
    print("Example 4: List and Query")
    print("="*60)
    
    repo = SqliteAgentsRuntimeRepository(db_path="./examples_agents.db")
    
    # List all agents
    agents = repo.list_agents()
    print(f"✓ Total agents: {len(agents)}")
    for agent in agents:
        print(f"  - {agent.agent_id}: {agent.agent_name}")
    
    # List runtimes for an agent
    if agents:
        agent_id = agents[0].agent_id
        runtimes = repo.list_agent_runtimes(agent_id)
        print(f"\n✓ Runtimes for {agent_id}: {len(runtimes)}")
        for runtime in runtimes:
            print(f"  - {runtime.agent_run_id}: {runtime.status}")
            
            # List tool calls for runtime
            tool_calls = repo.list_agent_runtime_tool_calls(agent_id, runtime.agent_run_id)
            print(f"    Tool calls: {len(tool_calls)}")
            for tool_call in tool_calls:
                print(f"      - {tool_call.tool_use_id}: {tool_call.tool_name}")
    
    repo.close()


def example_5_cascading_deletes():
    """Example 5: Demonstrate cascading deletes."""
    print("\n" + "="*60)
    print("Example 5: Cascading Deletes")
    print("="*60)
    
    repo = SqliteAgentsRuntimeRepository(db_path="./examples_agents.db")
    
    # Create test data
    agent = AgentsRuntimeMeta(agent_id="temp-agent")
    repo.update_agent(agent)
    
    runtime = AgentsRuntime(agent_id="temp-agent")
    repo.update_agent_runtime("temp-agent", runtime)
    
    tool_call = AgentsRuntimeToolCall(
        tool_use_id="temp-call",
        tool_name="test_tool",
    )
    repo.update_agent_runtime_tool_call("temp-agent", runtime.agent_run_id, tool_call)
    
    print(f"✓ Created test data")
    print(f"  Agents: {len(repo.list_agents())}")
    print(f"  Runtimes: {len(repo.list_agent_runtimes('temp-agent'))}")
    print(f"  Tool calls: {len(repo.list_agent_runtime_tool_calls('temp-agent', runtime.agent_run_id))}")
    
    # Delete agent (cascades to runtimes and tool calls)
    repo.delete_agent("temp-agent")
    print(f"\n✓ Deleted agent 'temp-agent'")
    print(f"  Agents: {len(repo.list_agents())}")
    print(f"  Runtimes: {len(repo.list_agent_runtimes('temp-agent'))}")
    print(f"  Tool calls: {len(repo.list_agent_runtime_tool_calls('temp-agent', runtime.agent_run_id))}")
    
    repo.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("SqliteAgentsRuntimeRepository Examples")
    print("="*60)
    
    example_1_basic_agent_storage()
    example_2_agent_runtime_execution()
    example_3_tool_calls_tracking()
    example_4_list_and_query()
    example_5_cascading_deletes()
    
    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")

