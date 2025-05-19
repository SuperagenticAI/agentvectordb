import pytest
from agentvectordb import AgentVectorDBStore, AsyncAgentVectorDBStore


def test_store_initialization(unique_test_db_path):
    store = AgentVectorDBStore(db_path=unique_test_db_path)
    assert store.db_path == unique_test_db_path
    assert store.db is not None


def test_store_list_collections(sync_store: AgentVectorDBStore, test_embedding_function):
    assert sync_store.list_collections() == []


@pytest.mark.asyncio
async def test_async_store_initialization(unique_test_db_path):
    store = AsyncAgentVectorDBStore(db_path=unique_test_db_path)
    assert store.db_path == unique_test_db_path
