# FivcPlayground

An intelligent agent ecosystem built on **Strands** for autonomous tool generation, task assessment, and dynamic agent orchestration.

> **🔄 Dual Backend Support**: FivcPlayground supports both **Strands** (default) and **LangChain** backends. See [Backend Selection Guide](docs/BACKEND_SELECTION.md) for details on switching backends.

## 🎯 Overview

FivcPlayground provides a flexible multi-agent system that can:
- **Assess tasks** intelligently to determine the best approach
- **Retrieve and use tools** dynamically based on task requirements
- **Plan and execute** complex workflows with specialized agents
- **Generate and optimize** tools autonomously
- **Chat and assist** users through an interactive web interface

## 🚀 Quickstart

### Prerequisites
- Python 3.10 or higher
- API keys for LLM providers (OpenAI, Ollama, etc.)

### Installation

```bash
# Install with uv (recommended)
make install        # runtime + dev dependencies

# Or minimal installation
make install-min    # runtime only

# Or with pip
pip install -e .
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Configure your LLM provider settings in `.env`:
```bash
# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Or Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

### Quick Start

```bash
# Launch the web interface
make serve

# Or run an agent from CLI
uv run fivcplayground run Generic --query "What is machine learning?"

# Show available commands
uv run fivcplayground --help
```

## 📁 Project Structure

```
src/fivcplayground/
├── agents/          # Agent creation and management
│   └── types/       # Agent retriever and creator types
├── backends/        # Backend implementations (langchain, strands)
│   ├── langchain/   # LangChain backend
│   └── strands/     # Strands backend
├── demos/           # Streamlit web interface
├── embeddings/      # Vector database and embeddings
│   └── types/       # Embedding database types
├── models/          # LLM model factories and providers
│   └── types/       # Model types and implementations
│       ├── repositories/  # Model configuration repositories
│       └── base.py        # ModelConfig data model
├── schemas.py       # Pydantic data schemas
├── settings/        # Configuration management
├── tasks.py         # Task execution functions
├── tools/           # Tool management and retrieval
│   └── types/       # Tool retriever and config types
└── utils/           # Utility functions

configs/             # Configuration examples
examples/            # Usage examples
├── agents/          # Agent usage examples
└── tools/           # Tool usage examples
tests/               # Test suite
docs/                # Documentation
```

## 💻 Usage

### Command Line Interface

```bash
# Show all available commands
fivcplayground --help

# Run an agent interactively
fivcplayground run Generic

# Run an agent with a specific query
fivcplayground run Generic --query "What is machine learning?"

# Run different agent types
fivcplayground run Companion --query "Tell me a joke"
fivcplayground run Consultant --query "How should I approach this task?"

# Clean temporary files
fivcplayground clean

# Show system information
fivcplayground info
```

### Available Agents

- **Generic** - Standard agent for general task execution
- **Companion** - Friendly chat agent for conversations
- **Tooling** - Specialized in finding the right tools
- **Consultant** - Assesses tasks and recommends approaches
- **Planner** - Creates execution plans and teams
- **Researcher** - Analyzes patterns and workflows
- **Engineer** - Develops and optimizes tools
- **Evaluator** - Assesses performance and quality

### Web Interface

FivcPlayground includes a modern web interface built with Streamlit:

```bash
# Launch web interface (default: localhost:8501)
fivcplayground web

# Or using Make
make serve

# Development mode with auto-reload
make serve-dev

# Custom port and host
fivcplayground web --port 8080 --host 0.0.0.0
```

**Features:**
- 💬 **Interactive chat interface** - Natural conversation with agents
- 🔄 **Async execution** - Non-blocking, responsive interface
- 🛠️ **Tool integration** - Automatic tool selection and execution
- 📝 **Conversation history** - Full session management
- 🎨 **Modern UI** - Clean, intuitive Streamlit interface

See [Web Interface Documentation](docs/WEB_INTERFACE.md) for detailed usage instructions.

## 🧰 Available Tools

FivcPlayground includes built-in tools and supports MCP (Model Context Protocol) tools:

**Built-in Tools:**
- `calculator` - Mathematical calculations
- `current_time` - Current date and time
- `python_repl` - Python code execution

**MCP Tools:**
Configure MCP servers in `configs/mcp.yaml` to add additional tools dynamically.

## 📚 Documentation

For comprehensive documentation, see the [docs/](docs/) directory:

- **[System Design](docs/DESIGN.md)** - Architecture and design principles
- **[Backend Selection Guide](docs/BACKEND_SELECTION.md)** - Switching between Strands and LangChain backends
- **[Web Interface Guide](docs/WEB_INTERFACE.md)** - Complete web interface usage
- **[Dependencies](docs/DEPENDENCIES.md)** - Installation and dependency management
- **[Quick Start](docs/QUICK_START.md)** - Getting started with FivcPlayground
- **[Documentation Index](docs/README.md)** - Complete documentation overview

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📄 License

MIT
