import pytest

from agentvectordb import AsyncAgentMemoryCollection, AsyncAgentVectorDBStore


@pytest.mark.asyncio
async def test_async_store_get_or_create_collection(async_store: AsyncAgentVectorDBStore, test_embedding_function):
    coll_name = "async_coll_for_store_test"
    collection1 = await async_store.get_or_create_collection(name=coll_name, embedding_function=test_embedding_function)
    assert isinstance(collection1, AsyncAgentMemoryCollection)
    assert collection1.name == coll_name
    assert coll_name in await async_store.list_collections()

    # Get existing (should hit cache in underlying sync store, wrapped again)
    collection2 = await async_store.get_or_create_collection(name=coll_name, embedding_function=test_embedding_function)
    assert collection1._sync_collection is collection2._sync_collection  # Underlying sync obj is same

    # Test recreate
    collection3 = await async_store.get_or_create_collection(
        name=coll_name, embedding_function=test_embedding_function, recreate=True
    )
    assert collection3._sync_collection is not collection1._sync_collection


@pytest.mark.asyncio
async def test_async_store_list_and_delete_collections(async_store: AsyncAgentVectorDBStore, test_embedding_function):
    assert await async_store.list_collections() == []
    await async_store.get_or_create_collection(name="async_c1", embedding_function=test_embedding_function)
    await async_store.get_or_create_collection(name="async_c2", embedding_function=test_embedding_function)

    collections = await async_store.list_collections()
    assert len(collections) == 2 and "async_c1" in collections and "async_c2" in collections

    assert await async_store.delete_collection("async_c1") is True
    assert "async_c1" not in await async_store.list_collections()
    assert len(await async_store.list_collections()) == 1
