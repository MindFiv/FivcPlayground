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
    "IEmbeddingDoc",
    "IEmbeddingResult",
    "IEmbeddingDB",
    "IEmbeddingDBProvider",
    "IModel",
    "IModelProvider",
    "ISetting",
    "ISettingProvider",
    "ITool",
    "IToolBundle",
    "IToolRetriever",
    "IToolRetrieverProvider",
]

from .embeddings import (
    IEmbeddingDoc,
    IEmbeddingResult,
    IEmbeddingDB,
    IEmbeddingDBProvider,
)
from .models import IModel, IModelProvider
from .settings import ISetting, ISettingProvider
from .tools import (
    ITool,
    IToolBundle,
    IToolRetriever,
    IToolRetrieverProvider,
)
