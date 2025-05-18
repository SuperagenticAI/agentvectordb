import pytest
from agentvector import AgentVectorStore, AgentMemoryCollection, AsyncAgentVectorStore
from agentvector.exceptions import InitializationError
from .conftest import test_embedding_function # Import fixture to make it available

# Synchronous Store Tests
def test_store_initialization(unique_test_db_path):
    store = AgentVectorStore(db_path=unique_test_db_path)
    assert store.db_path == unique_test_db_path
    assert store.db is not None # Check LanceDB connection object

def test_store_get_or_create_collection(sync_store: AgentVectorStore, test_embedding_function):
    coll_name = "test_coll_1"
    collection1 = sync_store.get_or_create_collection(
        name=coll_name, embedding_function=test_embedding_function
    )
    assert isinstance(collection1, AgentMemoryCollection)
    assert collection1.name == coll_name
    assert coll_name in sync_store.list_collections()

    # Get existing collection
    collection2 = sync_store.get_or_create_collection(
        name=coll_name, embedding_function=test_embedding_function
    )
    assert collection1 is collection2 # Should return cached instance for MVP

    # Test recreate
    collection3 = sync_store.get_or_create_collection(
        name=coll_name, embedding_function=test_embedding_function, recreate=True
    )
    assert collection3 is not collection1 # Should be a new instance after recreation
    assert collection3.name == coll_name

def test_store_list_collections(sync_store: AgentVectorStore, test_embedding_function):
    assert sync_store.list_collections() == []
    sync_store.get_or_create_collection(name="coll_a", embedding_function=test_embedding_function)
    sync_store.get_or_create_collection(name="coll_b", embedding_function=test_embedding_function)
    
    collections = sync_store.list_collections()
    assert len(collections) == 2
    assert "coll_a" in collections
    assert "coll_b" in collections

def test_store_delete_collection(sync_store: AgentVectorStore, test_embedding_function):
    coll_name = "to_delete"
    sync_store.get_or_create_collection(name=coll_name, embedding_function=test_embedding_function)
    assert coll_name in sync_store.list_collections()

    assert sync_store.delete_collection(coll_name) is True
    assert coll_name not in sync_store.list_collections()
    assert sync_store.delete_collection("non_existent_coll") is True # Idempotent

def test_store_get_collection_limitations(sync_store: AgentVectorStore, test_embedding_function):
    # MVP get_collection primarily relies on cache or very simple re-open.
    # This test highlights its current behavior.
    coll_name = "my_existing_collection"
    # Create it so it's in cache and on disk
    created_coll = sync_store.get_or_create_collection(name=coll_name, embedding_function=test_embedding_function)
    
    # Get from cache
    cached_coll = sync_store.get_collection(coll_name)
    assert cached_coll is created_coll

    # Simulate store re-init (clears cache) and try to get
    new_store_instance = AgentVectorStore(db_path=sync_store.db_path)
    # The collection exists on disk, but get_collection in MVP might not fully rehydrate it
    # with correct EF, schema, etc., without those params.
    # Current get_collection returns None for non-cached, existing-on-disk collections.
    reopened_coll = new_store_instance.get_collection(coll_name)
    assert reopened_coll is None # As per current MVP get_collection implementation detail

    # Correct way to access existing table with new store instance
    properly_reopened_coll = new_store_instance.get_or_create_collection(
        name=coll_name,
        embedding_function=test_embedding_function # Must provide original config
    )
    assert properly_reopened_coll is not None
    assert properly_reopened_coll.name == coll_name

# Asynchronous Store Tests
@pytest.mark.asyncio
async def test_async_store_initialization(unique_test_db_path):
    async_store = AsyncAgentVectorStore(db_path=unique_test_db_path)
    assert async_store.db_path == unique_test_db_path
    assert async_store._sync_store.db is not None # Check underlying sync store's DB connection

@pytest.mark.asyncio
async def test_async_store_get_or_create_collection(async_store: AsyncAgentVectorStore, test_embedding_function):
    coll_name = "async_test_coll_1"
    collection1 = await async_store.get_or_create_collection(
        name=coll_name, embedding_function=test_embedding_function
    )
    assert collection1 is not None # It's an AsyncAgentMemoryCollection
    assert collection1.name == coll_name
    # To check if it's in the underlying sync store's cache or disk:
    assert coll_name in await async_store.list_collections()

    collection2 = await async_store.get_or_create_collection(
        name=coll_name, embedding_function=test_embedding_function
    )
    # For async, these are new wrapper instances, but might wrap the same sync collection.
    # Asserting underlying sync collection instance is the same (if not recreated).
    assert collection1._sync_collection is collection2._sync_collection

    collection3 = await async_store.get_or_create_collection(
        name=coll_name, embedding_function=test_embedding_function, recreate=True
    )
    assert collection3._sync_collection is not collection1._sync_collection

@pytest.mark.asyncio
async def test_async_store_list_and_delete_collections(async_store: AsyncAgentVectorStore, test_embedding_function):
    assert await async_store.list_collections() == []
    await async_store.get_or_create_collection(name="async_coll_a", embedding_function=test_embedding_function)
    await async_store.get_or_create_collection(name="async_coll_b", embedding_function=test_embedding_function)
    
    collections = await async_store.list_collections()
    assert len(collections) == 2
    assert "async_coll_a" in collections

    assert await async_store.delete_collection("async_coll_a") is True
    assert "async_coll_a" not in await async_store.list_collections()