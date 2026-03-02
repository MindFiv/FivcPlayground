# FivcPlayground Web Interface

**Generated:** 2026-01-26
**Commit:** N/A
**Branch:** N/A

## OVERVIEW
Modern Streamlit web interface for FivcPlayground agent ecosystem with chat, task management, and custom navigation.

## STRUCTURE
```
plays/
├── components/      # Reusable UI components
│   └── chat_message.py    # Message rendering with thinking/tool display
├── utils/           # State management utilities
│   └── chats.py          # Chat session and agent execution logic
├── views/           # Page views and navigation
│   ├── base.py           # Custom ViewNavigation system
│   ├── chats.py          # Chat interface with streaming
│   └── tasks.py          # Task management page
└── assets/          # Static assets (logos, images)
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Custom navigation | `views/base.py` | ViewNavigation class replacing st.navigation |
| Chat interface | `views/chats.py` | Main conversation interface with streaming |
| Message rendering | `components/chat_message.py` | Tool calls, thinking blocks, streaming |
| Chat state management | `utils/chats.py` | ChatManager and Chat classes |
| Web app entry point | `__init__.py` | Backend setup and view routing |
| Task management | `views/tasks.py` | Multi-agent task interface |

## CONVENTIONS

### View Architecture
- All views inherit from `ViewBase` abstract class
- Custom `ViewNavigation` replaces st.navigation for better control
- State persistence via Streamlit session state and run.yml
- Automatic page detection from session state with fallback hierarchy

### Component Design
- Reusable components in `components/` directory
- ChatMessage handles streaming responses and tool call visualization
- CSS embedded in components for self-contained styling
- Session state used for streaming content accumulation

### Chat System
- ChatManager handles multiple chat sessions and agent creation
- Chat class encapsulates single conversation state and execution
- Automatic agent briefing and session metadata generation
- Async-first design with sync wrappers for Streamlit compatibility

## ANTI-PATTERNS (THIS PROJECT)

### Forbidden Patterns
- Don't use st.navigation - use ViewNavigation instead
- Don't create views without inheriting from ViewBase
- Don't bypass ChatManager for agent creation
- Don't use global Streamlit state without session keys

### Deprecated Practices
- Direct st.page_config calls after component imports
- Hardcoded navigation lists - build dynamically
- Sync-only agent execution - use async patterns
- CSS in separate files - embed in components