from .store import AgentVectorStore
from .collection import AgentMemoryCollection
from .async_store import AsyncAgentVectorStore
from .async_collection import AsyncAgentMemoryCollection
from .schemas import MemoryEntrySchema, create_dynamic_memory_entry_schema
from .exceptions import (
    AgentVectorException,
    InitializationError,
    SchemaError,
    QueryError,
    OperationError,
    EmbeddingError,
)
from . import utils
from . import embeddings

__version__ = "0.3.0" # MVP version with Store/Collection API

__all__ = [
    # Core API
    "AgentVectorStore",
    "AgentMemoryCollection",
    "AsyncAgentVectorStore",
    "AsyncAgentMemoryCollection",
    # Schemas & Helpers
    "MemoryEntrySchema",
    "create_dynamic_memory_entry_schema",
    # Exceptions
    "AgentVectorException",
    "InitializationError",
    "SchemaError",
    "QueryError",
    "OperationError",
    "EmbeddingError",
    # Modules
    "utils",
    "embeddings",
    "__version__"
]