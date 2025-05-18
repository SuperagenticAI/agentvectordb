import pytest
import shutil
import os
import time
import numpy as np # For sample_vector if needed, though EF is preferred
from typing import List

from agentvector import AgentVectorStore, AgentMemoryCollection, AsyncAgentVectorStore, AsyncAgentMemoryCollection
from agentvector.embeddings import DefaultTextEmbeddingFunction
from agentvector.schemas import MemoryEntrySchema, create_dynamic_memory_entry_schema

# --- Constants for Tests ---
# Note: Using a more unique prefix or a subdirectory within a standard test temp dir might be better
# For example, using pytest's tmp_path fixture for the root test DB dir.
# For now, this direct creation is simpler to illustrate.
TEST_DB_ROOT_DIR_PREFIX = "_test_agentvector_dbs_"
VECTOR_DIMENSION_TEST = 16 # Small dimension for faster tests

# --- Embedding Function Fixture ---
@pytest.fixture(scope="session")
def test_embedding_function():
    """Provides a consistent DefaultTextEmbeddingFunction for the entire test session."""
    return DefaultTextEmbeddingFunction(dimension=VECTOR_DIMENSION_TEST)

@pytest.fixture(scope="session")
def get_embedding_vec(test_embedding_function):
    """Helper to get a single vector from the test EF."""
    def _get_vec(text: str) -> List[float]:
        return test_embedding_function.generate([text])[0]
    return _get_vec

# --- Test Directory Management ---
@pytest.fixture(scope="function") # Changed to function scope for better isolation
def unique_test_db_path():
    """Creates a unique DB directory for each test function and cleans it up afterwards."""
    # Using time_ns and pid for uniqueness, good for parallel test runs too if they happen.
    # Storing in a general test temp area might be cleaner if system has one (e.g. /tmp or pytest's tmp_path).
    # For simplicity, creating directly in current dir for now.
    dir_name = f"{TEST_DB_ROOT_DIR_PREFIX}{time.time_ns()}_{os.getpid()}"
    full_path = os.path.join(os.getcwd(), dir_name) # Make it absolute or relative as preferred
    os.makedirs(full_path, exist_ok=True)
    # print(f"\n[Test Setup] Created DB dir: {full_path}") # For debugging test setup
    yield full_path
    # print(f"[Test Teardown] Removing DB dir: {full_path}") # For debugging test teardown
    shutil.rmtree(full_path, ignore_errors=True)


# --- Synchronous Store and Collection Fixtures ---
@pytest.fixture
def sync_store(unique_test_db_path: str) -> AgentVectorStore:
    """Provides a clean AgentVectorStore instance for each test function."""
    return AgentVectorStore(db_path=unique_test_db_path)

@pytest.fixture
def sync_collection(sync_store: AgentVectorStore, test_embedding_function) -> AgentMemoryCollection:
    """Provides a default, clean AgentMemoryCollection from the sync_store."""
    # Using a fixed name as the db_path is unique per test
    return sync_store.get_or_create_collection(
        name="default_sync_collection",
        embedding_function=test_embedding_function,
        recreate=True # Ensure it's always fresh for the test
    )

@pytest.fixture
def sync_collection_ts_update(sync_store: AgentVectorStore, test_embedding_function) -> AgentMemoryCollection:
    """Provides a collection with timestamp_last_accessed updates enabled."""
    return sync_store.get_or_create_collection(
        name="sync_collection_ts",
        embedding_function=test_embedding_function,
        update_last_accessed_on_query=True, # Key difference
        recreate=True
    )

# --- Asynchronous Store and Collection Fixtures ---
@pytest.fixture
async def async_store(unique_test_db_path: str) -> AsyncAgentVectorStore:
    """Provides a clean AsyncAgentVectorStore instance for each async test function."""
    # AsyncAgentVectorStore itself initializes a sync store, so db_path needs to be unique.
    return AsyncAgentVectorStore(db_path=unique_test_db_path)

@pytest.fixture
async def async_collection(async_store: AsyncAgentVectorStore, test_embedding_function) -> AsyncAgentMemoryCollection:
    """Provides a default, clean AsyncAgentMemoryCollection."""
    return await async_store.get_or_create_collection(
        name="default_async_collection",
        embedding_function=test_embedding_function,
        recreate=True
    )

@pytest.fixture
async def async_collection_ts_update(async_store: AsyncAgentVectorStore, test_embedding_function) -> AsyncAgentMemoryCollection:
    """Provides an async collection with timestamp_last_accessed updates enabled."""
    return await async_store.get_or_create_collection(
        name="async_collection_ts",
        embedding_function=test_embedding_function,
        update_last_accessed_on_query=True,
        recreate=True
    )

# --- Custom Schema for Testing ---
class MyTestSchema(MemoryEntrySchema):
    custom_text: Optional[str] = None
    custom_int: Optional[int] = Field(default=None, ge=0)

@pytest.fixture(scope="session")
def custom_schema_fixture():
    return MyTestSchema