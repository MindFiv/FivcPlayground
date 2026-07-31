# FivcPlayground Dependencies Guide

This document explains the dependency structure and installation options for FivcPlayground.

## 📁 Dependency Management

FivcPlayground uses modern Python dependency management with:
- **`pyproject.toml`** - Primary dependency specification (source of truth)
- **`uv.lock`** - Lock file for reproducible builds
- **`uv`** - Fast Python package manager (recommended)

## 🚀 Installation Options

### 1. Using UV (Recommended)
For the best experience with fast dependency resolution:

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Minimal installation (core only, no backends)
uv sync

# With ChromaDB embedding backend
uv sync --extra chroma

# With LangChain agent backend
uv sync --extra langchain

# With Strands agent backend
uv sync --extra strands

# With Google ADK agent backend
uv sync --extra adk

# With everything (all backends + embeddings)
uv sync --extra all

# With development dependencies
uv sync --extra dev
```

### 2. Using Make (Convenient)
We provide convenient Make targets:

```bash
# Basic installation (core only)
make install

# Minimal installation (runtime only)
make install-min

# Development installation
make dev
```

### 3. Using pip (Traditional)
If you prefer using pip:

```bash
# Minimal installation (core only)
pip install -e .

# With ChromaDB embedding backend
pip install -e ".[chroma]"

# With LangChain agent backend
pip install -e ".[langchain]"

# With Strands agent backend
pip install -e ".[strands]"

# With Google ADK agent backend
pip install -e ".[adk]"

# With everything (all backends + embeddings)
pip install -e ".[all]"

# With development dependencies
pip install -e ".[dev]"

# Combined installation (e.g., LangChain + ChromaDB + dev)
pip install -e ".[langchain,chroma,dev]"
```

## 📦 Dependency Categories

### Core Runtime Dependencies (Always Installed)
| Package | Version | Purpose |
|---------|---------|---------|
| typer | >=0.12.3 | CLI framework |
| rich | >=13.7.1 | Terminal formatting |
| pydantic | >=2.7.0 | Data validation |
| PyYAML | >=6.0.1 | Configuration files |
| python-dotenv | >=1.0.1 | Environment variables |
| openai | >=1.109.1 | OpenAI API client |
| nest-asyncio | >=1.6.0 | Async event loop support |
| httpx | >=0.28.1 | HTTP client |

### ChromaDB Embedding Backend (`[chroma]`)
| Package | Version | Purpose |
|---------|---------|---------|
| chromadb | >=1.1.0 | Vector database for embeddings |
| langchain-text-splitters | >=0.3.11 | Text chunking for embeddings |

### LangChain Agent Backend (`[langchain]`)
| Package | Version | Purpose |
|---------|---------|---------|
| langchain | >=1.2.0 | LangChain framework |
| langchain-core | >=1.2.0 | LangChain core abstractions |
| langchain-community | >=0.4.1 | LangChain community integrations |
| langchain-openai | >=1.0.0 | LangChain OpenAI integration |
| langgraph | >=1.0.5 | LangChain graph framework |
| langchain-mcp-adapters | >=0.2.1 | MCP tool integration for LangChain |
| langchain-ollama | >=1.0.0 | LangChain Ollama integration |
| langchain-text-splitters | >=0.3.11 | Text processing utilities |

### Strands Agent Backend (`[strands]`)
| Package | Version | Purpose |
|---------|---------|---------|
| strands-agents | >=1.20.0 | Strands AI agent framework |

### Google ADK Agent Backend (`[adk]`)
| Package | Version | Purpose |
|---------|---------|---------|
| google-adk | - | Google AI agent framework |

### Convenience Groups
| Group | Contents | Purpose |
|-------|----------|---------|
| `[all]` | ChromaDB, Google ADK, Strands, all model providers | Complete installation with everything |
| `[dev]` | Testing and development tools | Development and testing |

### Development Dependencies (`[dev]`)
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.2.0 | Testing framework |
| pytest-asyncio | >=0.21.0 | Async testing support |
| pytest-cov | >=4.1.0 | Test coverage reporting |
| pytest-benchmark | >=5.1.0 | Performance benchmarking |
| ruff | >=0.4.0,<0.6 | Linting and formatting |
| build | >=1.0.0 | Build system |
| twine | >=4.0.0 | Package publishing |

## 🔄 Backend Selection

FivcPlayground supports multiple agent frameworks and embedding backends. Install only what you need:

### Agent Backends

#### Strands Backend
- Uses `strands-agents` framework
- Optimized for agent orchestration
- Install with: `pip install ".[strands]"`

#### Google ADK Backend
- Uses `google-adk` framework
- Google's AI agent framework
- Install with: `pip install ".[adk]"`

#### LangChain Backend
- Uses `langchain-core` framework
- Broader ecosystem integration
- Install with: `pip install ".[langchain]"`

### Embedding Backends

#### ChromaDB Backend
- Vector database for semantic search
- Used by ToolRetriever for tool selection
- Install with: `pip install ".[chroma]"`

### Using Different Backends

Backend selection is done explicitly when creating backend instances:

```python
# Using Strands agent backend
from fivcplayground.backends.strands import StrandsAgentBackend
agent_backend = StrandsAgentBackend()

# Using Google ADK agent backend
from fivcplayground.backends.adk import AdkAgentBackend
agent_backend = AdkAgentBackend()

# Using LangChain agent backend
from fivcplayground.backends.langchain import LangchainAgentBackend
agent_backend = LangchainAgentBackend()

# Using ChromaDB embedding backend
from fivcplayground.backends.chroma import ChromaEmbeddingBackend
embedding_backend = ChromaEmbeddingBackend()
```

### Installation Examples

```bash
# Minimal installation (core only, no backends)
pip install -e .

# Strands agent + ChromaDB embeddings
pip install -e ".[strands,chroma]"

# Google ADK agent + ChromaDB embeddings
pip install -e ".[adk,chroma]"

# LangChain agent + ChromaDB embeddings
pip install -e ".[langchain,chroma]"

# Everything (all backends + embeddings)
pip install -e ".[all]"

# Development setup with all backends
pip install -e ".[all,dev]"
```

## 🔧 Dependency Management

### Updating Dependencies
1. Update `pyproject.toml` (source of truth)
2. Run `uv sync` to update lock file
3. Test in clean environment

### Adding New Dependencies
1. Add to appropriate section in `pyproject.toml`
2. Run `uv sync` to install and update lock file
3. Test installation in clean environment
4. Update this documentation

### Version Pinning Strategy
- **Core dependencies**: Use minimum versions with `>=`
- **Development tools**: Pin to specific ranges when needed
- **Lock file**: Provides exact versions for reproducible builds

## 🔍 Troubleshooting

### Common Issues
1. **Python version**: FivcPlayground requires Python 3.10+
2. **UV installation**: Install uv from https://astral.sh/uv/
3. **Virtual environment**: UV automatically manages virtual environments

### Solutions
```bash
# Check Python version
python --version

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clean install
rm -rf .venv uv.lock
uv sync

# Check installation
uv run fivcplayground --help
```

## 📊 Dependency Analysis
To analyze dependencies:

```bash
# Show dependency tree
uv tree

# Show outdated packages
uv sync --upgrade

# Export requirements for compatibility
uv export --format requirements-txt > requirements.txt
```

## 🔄 Maintenance

### Regular Tasks
- **Monthly**: Run `uv sync --upgrade` to check for updates
- **Before releases**: Full dependency audit and testing
- **Security**: Monitor for security advisories

### Best Practices
- Always use `uv sync` after pulling changes
- Keep `uv.lock` in version control for reproducible builds
- Test in clean environments before releases
- Use package managers (uv, pip) instead of manually editing pyproject.toml
- Run `make install` for consistent development setup

## 📝 Dependency Notes

### Strands Framework
FivcPlayground is built on the Strands framework:
- `strands-agents>=1.9.1`: Core agent framework with async support
- `strands-agents-tools>=0.2.8`: Built-in tools and MCP integration

### Python Version
- Minimum: Python 3.10
- Recommended: Python 3.11 or 3.12
- Uses modern Python features (type hints, async/await, pattern matching)

This modern dependency management ensures FivcPlayground remains maintainable and secure.

---

**Last Updated**: 2025-10-16
**Version**: 0.1.0
