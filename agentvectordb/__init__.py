from . import embeddings, utils
from .agent_memory import AgentMemory  # Add this import
from .async_agent_memory import AsyncAgentMemory  # Add this import
from .async_collection import AsyncAgentMemoryCollection
from .async_store import AsyncAgentVectorDBStore
from .collection import AgentMemoryCollection
from .exceptions import (
    AgentVectorDBException,
    EmbeddingError,
    InitializationError,
    OperationError,
    QueryError,
    SchemaError,
)
from .schemas import MemoryEntrySchema, create_dynamic_memory_entry_schema
from .store import AgentVectorDBStore

__version__ = "0.3.0"  # MVP version with Store/Collection API

__all__ = [
    # Core API
    "AgentVectorDBStore",
    "AgentMemoryCollection",
    "AsyncAgentVectorDBStore",
    "AsyncAgentMemoryCollection",
    "AgentMemory",  # Add this
    "AsyncAgentMemory",  # Add this
    # Schemas & Helpers
    "MemoryEntrySchema",
    "create_dynamic_memory_entry_schema",
    # Exceptions
    "AgentVectorDBException",
    "InitializationError",
    "SchemaError",
    "QueryError",
    "OperationError",
    "EmbeddingError",
    # Modules
    "utils",
    "embeddings",
    "__version__",
]
