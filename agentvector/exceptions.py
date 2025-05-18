class AgentVectorException(Exception):
    """Base exception for AgentVector errors."""
    pass

class InitializationError(AgentVectorException):
    """Error during Store or Collection initialization."""
    pass

class SchemaError(AgentVectorException):
    """Error related to data schemas or Pydantic validation."""
    pass

class QueryError(AgentVectorException):
    """Error during querying."""
    pass

class OperationError(AgentVectorException):
    """Error during add, update, or delete operations."""
    pass

class EmbeddingError(AgentVectorException):
    """Error related to vector embedding generation or handling."""
    pass