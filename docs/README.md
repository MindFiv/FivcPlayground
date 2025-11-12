# FivcPlayground Documentation

Welcome to the FivcPlayground documentation! This directory contains comprehensive guides and technical documentation for the FivcPlayground intelligent agent ecosystem built on the Strands framework.

## 📚 Documentation Index

### Core Documentation

#### [🎯 DESIGN.md](DESIGN.md)
**System Architecture and Design Principles**
- Overview of FivcPlayground's architecture based on Strands
- Agent system and specialized agent types
- Tool management and retrieval
- Core features and workflows
- Technical implementation details

#### [🌐 WEB_INTERFACE.md](WEB_INTERFACE.md)
**Web Interface User Guide**
- Getting started with the multi-page Streamlit interface
- Multi-chat management and navigation
- Feature overview and usage instructions
- Component-based architecture guide
- Development and customization guide
- Persistence and storage details
- Troubleshooting and integration

#### [📦 DEPENDENCIES.md](DEPENDENCIES.md)
**Dependency Management Guide**
- Installation options (uv, pip, make)
- Complete dependency list with versions
- Troubleshooting and maintenance
- Best practices for development

## 🚀 Quick Start

### For Users
1. **Installation**: Start with [DEPENDENCIES.md](DEPENDENCIES.md) for setup instructions
2. **Getting Started**: Read [WEB_INTERFACE.md](WEB_INTERFACE.md) for web interface usage
3. **Understanding the System**: Review [DESIGN.md](DESIGN.md) for architecture overview

### For Developers
1. **Setup**: Start with [DEPENDENCIES.md](DEPENDENCIES.md) for development environment
2. **Architecture**: Study [DESIGN.md](DESIGN.md) for system design and components
3. **Web Interface**: Review [WEB_INTERFACE.md](WEB_INTERFACE.md) for interface development
4. **Examples**: Check `../examples/` directory for code examples

## 📖 Documentation Categories

### 🏗️ Architecture & Design
- **[DESIGN.md](DESIGN.md)**: System architecture, agent types, tool management, and workflows

### 🔧 Setup & Operations
- **[DEPENDENCIES.md](DEPENDENCIES.md)**: Installation, dependency management, and troubleshooting
- **[WEB_INTERFACE.md](WEB_INTERFACE.md)**: Streamlit web interface usage and development

### 🎯 By Use Case

#### New Users
1. Start with [DEPENDENCIES.md](DEPENDENCIES.md) for installation
2. Launch the web interface following [WEB_INTERFACE.md](WEB_INTERFACE.md)
3. Try example queries to understand capabilities
4. Review [DESIGN.md](DESIGN.md) for system understanding

#### Developers
1. Set up development environment with [DEPENDENCIES.md](DEPENDENCIES.md)
2. Study system architecture in [DESIGN.md](DESIGN.md)
3. Explore agent and tool APIs
4. Review web interface code in [WEB_INTERFACE.md](WEB_INTERFACE.md)
5. Check `../examples/` for code samples

#### System Administrators
1. Review [DEPENDENCIES.md](DEPENDENCIES.md) for deployment requirements
2. Configure LLM providers and API keys
3. Set up MCP tools if needed
4. Deploy web interface following [WEB_INTERFACE.md](WEB_INTERFACE.md)

## 🔗 Related Resources

### Main Project
- **[../README.md](../README.md)**: Main project README with quick start guide
- **[../pyproject.toml](../pyproject.toml)**: Project dependencies and configuration
- **[../Makefile](../Makefile)**: Common development commands

### Code Examples
- **[../examples/agents/](../examples/agents/)**: Agent usage examples
- **[../examples/tools/](../examples/tools/)**: Tool retrieval examples

### Configuration
- **[../configs/](../configs/)**: Configuration examples and templates
  - `mcp.yaml.example` - MCP tool configuration
  - `settings.yaml.example` - Application settings

### Testing
- **[../tests/](../tests/)**: Test suite and validation examples

## 📝 Contributing to Documentation

### Documentation Standards
- Use clear, concise language
- Include practical code examples
- Provide troubleshooting guidance
- Keep content synchronized with code changes
- Use emojis for visual organization
- Include command-line examples

### File Organization
- **DESIGN.md** - System architecture and technical design
- **DEPENDENCIES.md** - Installation and dependency management
- **WEB_INTERFACE.md** - Web interface usage and development
- **README.md** - Documentation index and navigation

### Updating Documentation
1. **Code Changes**: Update docs when modifying features
2. **New Features**: Add documentation for new capabilities
3. **Examples**: Update examples when APIs change
4. **Troubleshooting**: Add solutions for common issues
5. **Version Info**: Note breaking changes and migrations

## 🆘 Getting Help

### Documentation Issues
- Check the specific document's troubleshooting section
- Review related examples in the `../examples/` directory
- Consult the main project README for basic setup
- Search for similar issues in the project repository

### Technical Support
1. **Check Logs**: Review terminal output and error messages
2. **Configuration**: Verify environment variables and settings
3. **Examples**: Test with provided examples to isolate issues
4. **Dependencies**: Ensure all dependencies are installed correctly
5. **API Keys**: Verify LLM provider credentials are configured

### Common Resources
- **Main README**: [../README.md](../README.md)
- **Examples**: [../examples/](../examples/)
- **Configuration**: [../configs/](../configs/)

---

## 🆕 Recent Updates

### Version 0.1.0 (2025-10-16)
- **Multi-Page Web Interface**: New navigation system with dynamic chat pages
- **Chat Management**: ChatManager and Chat classes for multi-conversation support
- **Agent Runtime System**: Comprehensive persistence with AgentsRuntime models
- **File-Based Storage**: FileAgentsRuntimeRepository for organized data storage
- **Component Architecture**: Modular views, components, and managers
- **Streaming Support**: Real-time response updates with async execution
- **Tool Call Tracking**: Complete tool invocation history and visualization

---

**Last Updated**: 2025-10-16
**Version**: 0.1.0
**Framework**: Strands (strands-agents 1.9.1+)
**Maintainer**: FivcPlayground Team
