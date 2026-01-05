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

# Basic installation
uv sync

# With development dependencies
uv sync --extra dev
```

### 2. Using Make (Convenient)
We provide convenient Make targets:

```bash
# Basic installation
make install

# Minimal installation (runtime only)
make install-min

# Development installation
make dev
```

### 3. Using pip (Traditional)
If you prefer using pip:

```bash
# Basic installation
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## 📦 Dependency Categories

### Core Runtime Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| typer | >=0.12.3 | CLI framework |
| rich | >=13.7.1 | Terminal formatting |
| streamlit | >=1.49.1 | Web interface |
| pydantic | >=2.7.0 | Data validation |
| PyYAML | >=6.0.1 | Configuration files |
| python-dotenv | >=1.0.1 | Environment variables |
| httpx | >=0.28.1 | HTTP client |
| chromadb | >=1.1.0 | Vector database |
| audioread | >=3.0.1 | Audio file support |

### Agent Framework Dependencies (Strands - Default)
| Package | Version | Purpose |
|---------|---------|---------|
| strands-agents | >=1.9.1 | AI agent framework (default backend) |
| strands-agents-tools | >=0.2.8 | Agent tools library |

### LLM Provider Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| openai | >=1.109.1 | OpenAI API client |
| langchain-core | >=0.3.0 | LangChain core (alternative backend) |
| langchain-openai | >=0.2.0 | LangChain OpenAI integration |
| langchain-ollama | >=0.2.0 | LangChain Ollama integration |
| langchain-mcp-adapters | >=0.1.0 | MCP tool integration for LangChain |
| langchain-text-splitters | >=0.3.11 | Text processing utilities |

### Development Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.2.0 | Testing framework |
| pytest-asyncio | >=0.21.0 | Async testing support |
| pytest-cov | >=4.1.0 | Test coverage reporting |
| ruff | >=0.4.0,<0.6 | Linting and formatting |

## 🔄 Backend Selection

FivcPlayground supports two agent frameworks, and both are installed by default:

### Strands Backend (Default)
- Uses `strands-agents` framework
- Optimized for agent orchestration
- All dependencies included by default

### LangChain Backend (Alternative)
- Uses `langchain-core` framework
- Broader ecosystem integration
- All dependencies included by default

### Using Different Backends

Backend selection is done explicitly when creating backend instances:

```python
# Using Strands
from fivcplayground.backends.strands import StrandsAgentBackend
agent_backend = StrandsAgentBackend()

# Using LangChain
from fivcplayground.backends.langchain import LangchainAgentBackend
agent_backend = LangchainAgentBackend()
```

**Note**: Both backends are installed by default. No additional installation or configuration needed.

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

### Streamlit Version
- Requires Streamlit 1.49.1+ for `st.navigation` support
- Multi-page navigation is a core feature requiring this version

### Python Version
- Minimum: Python 3.10
- Recommended: Python 3.11 or 3.12
- Uses modern Python features (type hints, async/await, pattern matching)

This modern dependency management ensures FivcPlayground remains maintainable and secure.

---

**Last Updated**: 2025-10-16
**Version**: 0.1.0
