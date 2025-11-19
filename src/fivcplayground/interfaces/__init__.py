"""
Interfaces module for FivcPlayground.

This module defines the interface contracts for all major components in FivcPlayground,
enabling flexible component substitution through dependency injection.

Interfaces are organized by domain:
- settings: Configuration management interfaces
- repositories: Data persistence interfaces
- providers: Service provisioning interfaces
- tools: Tool management interfaces
"""

__all__ = [
    "EmbeddingDoc",
    "EmbeddingResult",
    "IEmbeddingDB",
    "IEmbeddingDBProvider",
    "IModel",
    "IModelProvider",
    "ModelConfig",
    "RunnableStatus",
    "RunnableContent",
    "RunnableTraceToolCall",
    "RunnableTrace",
    "RunnableProxy",
    "IRunnableCallback",
    "IRunnableSession",
    "IRunnable",
    "ISetting",
    "ISettingProvider",
    "ITool",
    "IToolBundle",
    "IToolProvider",
    "IAgent",
    "IAgentProvider",
    "AgentConfig",
]

from .embeddings import (
    EmbeddingDoc,
    EmbeddingResult,
    IEmbeddingDB,
    IEmbeddingDBProvider,
)
from .models import (
    IModel,
    IModelProvider,
    ModelConfig,
)
from .runnables import (
    RunnableStatus,
    RunnableContent,
    RunnableTraceToolCall,
    RunnableTrace,
    RunnableProxy,
    IRunnableCallback,
    IRunnableSession,
    IRunnable,
)
from .settings import (
    ISetting,
    ISettingProvider,
)
from .tools import (
    ITool,
    IToolBundle,
    IToolProvider,
)
from .agents import (
    IAgent,
    IAgentProvider,
    AgentConfig,
)
