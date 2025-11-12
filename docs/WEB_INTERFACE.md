# FivcPlayground Web Interface

FivcPlayground includes a modern, interactive web interface built with **Streamlit**, providing an intuitive multi-page application to interact with the intelligent agent ecosystem.

## 🚀 Quick Start

### Launch the Web Interface

```bash
# Using Make (recommended)
make serve

# Using CLI directly
uv run fivcplayground web

# Development mode with auto-reload
make serve-dev

# With custom options
uv run fivcplayground web --port 8080 --host 0.0.0.0
```

### Access the Interface

Once started, open your browser and navigate to:
- **Default**: http://localhost:8501
- **Custom**: http://localhost:[your-port]

## ✨ Features

### 💬 Multi-Chat Interface
- **Multiple Conversations**: Create and manage multiple independent chat sessions
- **Dynamic Navigation**: Each chat appears as a separate page in the sidebar
- **Natural Conversation**: Chat-based interaction with AI agents
- **Multi-turn Dialogue**: Context-aware conversations with full history
- **Async Execution**: Non-blocking interface that stays responsive
- **Streaming Responses**: Real-time response generation with live updates
- **Persistent History**: All conversations automatically saved to disk
- **Chat Descriptions**: Each chat displays a descriptive title in the navigation

### 🛠️ Tool Integration
- **Automatic Tool Selection**: Agent automatically chooses appropriate tools
- **Tool Execution Tracking**: Visual feedback for tool usage with status indicators
- **Built-in Tools**: Calculator, Python REPL, time utilities
- **MCP Tools**: Support for external MCP-compatible tools
- **Tool Results Display**: Clear presentation of tool inputs and outputs
- **Tool Call Rendering**: Expandable sections showing tool execution details

### 📊 User Interface
- **Multi-Page Navigation**: Organized pages for Chats and Settings
- **Clean Design**: Modern, intuitive Streamlit interface
- **Responsive Layout**: Adapts to different screen sizes
- **Component-Based**: Reusable UI components for consistency
- **Message Formatting**: Markdown support for rich text
- **Error Handling**: Graceful error messages and recovery
- **Auto-Refresh**: Page automatically updates when new chats are created

### 🔄 Persistence & State Management
- **File-Based Storage**: All data persisted in `.fivcplayground/agents/` directory
- **Agent Runtime Tracking**: Complete execution history with timestamps
- **Tool Call Persistence**: All tool invocations saved with inputs and results
- **Hierarchical Storage**: Organized directory structure for easy access
- **JSON Format**: Human-readable data storage
- **Automatic Cleanup**: Built-in cleanup commands for managing storage

## 💡 Example Queries

Try these sample queries to explore FivcPlayground's capabilities:

### General Questions
- "What is machine learning?"
- "Explain quantum computing in simple terms"
- "What are the benefits of renewable energy?"

### Code Generation
- "Write a Python function to calculate fibonacci numbers"
- "Create a function to sort a list of dictionaries by a key"
- "Show me how to read a CSV file in Python"

### Calculations
- "Calculate the compound interest on $10,000 at 5% for 10 years"
- "What is 15% of 250?"
- "Convert 100 USD to EUR"

### Information
- "What time is it?"
- "Tell me about the history of the internet"
- "Explain how neural networks work"

## 🎨 Interface Layout

The web interface features a modern multi-page layout with dynamic navigation:

### Navigation Structure
- **Sidebar Navigation**: Dynamic page list organized by category
  - **Chats Section**:
    - "New Chat" button to create new conversations
    - Individual pages for each existing chat (with descriptive titles)
  - **Settings Section**: Application configuration and preferences

### Page Layouts

#### Chat Pages
- **Page Title**: "💬 Chat with FivcPlayground"
- **Conversation History**: Scrollable list of all messages in chronological order
- **Message Display**:
  - User messages with "user" avatar
  - Agent messages with "assistant" avatar
  - Tool calls in expandable sections
  - Streaming text updates in real-time
- **Input Box**: Chat input field at the bottom ("Ask me anything...")
- **Auto-Navigation**: Automatically switches to new chat page after creation

#### Settings Page
- **Model Configuration**: LLM provider and model selection
- **Task Configuration**: Complexity thresholds and subtask limits
- **Session Management**: Cleanup and reset options
- **Settings Persistence**: Save and view current configuration

## 🔧 Development

### Running in Development Mode

```bash
# Development mode with auto-reload
make serve-dev

# Or directly with Streamlit
uv run streamlit run src/fivcplayground/app/__init__.py --server.port 8501
```

### Architecture

The web interface uses a modular, component-based architecture:

#### Directory Structure
```
src/fivcplayground/app/
├── __init__.py              # Main app with ViewNavigation setup
├── utils/                   # Utility classes and state management
│   ├── chats.py            # Chat and ChatManager classes
│   └── tasks.py            # Task monitoring (future)
├── views/                   # View implementations (inherit from ViewBase)
│   ├── base.py             # ViewBase and ViewNavigation
│   ├── chats.py            # ChatView implementation
│   ├── tasks.py            # TasksView implementation (future)
│   ├── settings/           # Settings views submodule
│   │   ├── __init__.py     # Settings views exports
│   │   ├── general.py      # GeneralSettingView implementation
│   │   └── mcp.py          # MCPSettingView implementation
│   └── __init__.py         # Views module exports
└── components/              # Reusable UI components
    └── chat_message.py     # Message and tool call rendering
```

#### Key Components

**1. Main Application (`__init__.py`)**
- Sets up page configuration
- Creates ChatManager instance
- Builds dynamic navigation with st.navigation
- Manages page routing and state

**2. Chat Utility (`utils/chats.py`)**
- `Chat` class: Manages individual chat sessions
  - Agent runtime creation and execution
  - Conversation history management
  - Streaming response handling
  - Persistence via AgentsRuntimeRepository
- `ChatManager` class: Manages multiple chats
  - Lists all existing chats
  - Creates new chat instances
  - Shares repository and tools across chats

**3. Views (`views/`)**
- `chats.render(chat)`: Renders chat interface for a specific Chat instance
- `settings.render()`: Renders settings and configuration page
- `tasks.render()`: Task monitoring view (future feature)

**4. Components (`components/`)**
- `ChatMessage(runtime).render(container)`: Renders a single message
  - Displays user query
  - Shows agent response with streaming support
  - Renders tool calls in expandable sections with status indicators
  - Handles different message states (pending, executing, completed)
  - Includes tool call rendering with inputs, outputs, and timing
  - Uses class-based architecture for better modularity

**5. Persistence Layer**
- `FileAgentsRuntimeRepository`: File-based storage
- Storage location: `.fivcplayground/agents/`
- Structure:
  ```
  .fivcplayground/agents/
  └── agent_<agent_id>/
      ├── agent.json                    # Agent metadata
      └── run_<timestamp>/
          ├── run.json                  # Runtime data
          └── tool_calls/
              └── tool_call_<id>.json   # Tool call records
  ```

### Customization

You can customize the interface by modifying:

**1. Chat Behavior** (`app/utils/chats.py`):
```python
# Modify Chat class to change agent behavior
- Default agent creation logic
- System prompts and agent configuration
- Streaming callback handling
- History filtering and display
```

**2. Page Layout** (`app/__init__.py`):
```python
# Customize navigation structure
- Add new page categories
- Modify page icons and titles
- Change default page selection
- Update page configuration (layout, theme, etc.)
```

**3. Message Rendering** (`app/components/chat_message.py`):
```python
# ChatMessage class for message display
- Class-based architecture with runtime initialization
- Message formatting and styling
- Tool call visualization with expandable sections
- Streaming text presentation with animated indicators
- Error message handling
- Tool execution status indicators
- Input/output formatting for tool calls
```

## 🔍 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Change to a different port
uv run fivcplayground web --port 8080
```

#### Dependencies Not Installed
```bash
# Install all dependencies
uv sync

# Or with make
make install
```

#### API Keys Not Configured
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# OPENAI_API_KEY=your_key_here
```

#### Slow Startup
- First run may be slower due to:
  - Model initialization
  - Tool loading
  - MCP server connections
  - ChromaDB initialization
- Subsequent runs will be faster

#### Chat Not Responding
1. Check terminal output for error messages
2. Verify API keys are configured correctly
3. Ensure LLM provider is accessible
4. Check network connectivity
5. Verify agent runtime repository is writable

#### Navigation Issues
- If new chats don't appear in sidebar, check:
  - Agent metadata was saved (check `.fivcplayground/agents/`)
  - Page refresh occurred (st.rerun() was called)
  - No errors in terminal output

#### Storage Issues
```bash
# Clear all agent data
rm -rf .fivcplayground/agents/*

# Or clean all temporary files
make clean

# Check storage location
ls -la .fivcplayground/agents/
```

#### Streaming Not Working
- Ensure async execution is working properly
- Check that on_event callback is being called
- Verify AgentsRuntime is being updated correctly
- Look for errors in terminal output

### Getting Help

- **Terminal Output**: Check for detailed error messages and stack traces
- **Storage Inspection**: Review agent data in `.fivcplayground/agents/`
- **Documentation**: Refer to [README.md](../README.md) and [DESIGN.md](DESIGN.md)
- **Issues**: Report bugs on the project repository

## 🔗 Integration

The web interface integrates seamlessly with:

### CLI Integration
```bash
# Launch from CLI
fivcplayground web

# Or with Make
make serve
```

### Agent System
- Uses the same agent creation system as CLI
- Shares AgentsRuntimeRepository for persistence
- Shares tool registry and retriever
- Consistent behavior across interfaces
- Same LLM configuration and models

### Configuration
- Respects environment variables (.env)
- Uses same settings files (settings.yaml)
- Shares agent storage directory
- Common tool configuration (mcp.yaml)

### Tool System
- Access to all registered tools
- MCP tool support with same configuration
- Dynamic tool loading and retrieval
- Shared tool execution environment

### Data Persistence
- All chats stored in `.fivcplayground/agents/`
- Compatible with CLI agent execution
- Can resume chats created via CLI
- Shared runtime history

This provides a unified experience across command-line and web interfaces, with all data and configuration shared between them.

---

**Last Updated**: 2025-10-16
**Version**: 0.1.0
**Framework**: Streamlit 1.49.1+, Strands (strands-agents 1.9.1+)
