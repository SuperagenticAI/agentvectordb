class AgentVectorDBException(Exception):
    """Base exception for AgentVectorDB errors."""
    pass

class InitializationError(AgentVectorDBException):
    """Error during Store or Collection initialization."""
    pass

class SchemaError(AgentVectorDBException):
    """Error related to data schemas or Pydantic validation."""
    pass

class QueryError(AgentVectorDBException):
    """Error during querying."""
    pass

class OperationError(AgentVectorDBException):
    """Error during add, update, or delete operations."""
    pass

class EmbeddingError(AgentVectorDBException):
    """Error related to vector embedding generation or handling."""
    pass