import pytest
import time
from .conftest import VECTOR_DIMENSION_TEST, test_embedding_function, get_embedding_vec # Import fixtures
from agentvectordb import AsyncAgentMemoryCollection # The class we are testing

@pytest.mark.asyncio
async def test_async_collection_add_and_get(async_collection: AsyncAgentMemoryCollection, get_embedding_vec):
    content = "Async add and get test"
    vector = get_embedding_vec(content)
    entry_id = await async_collection.add(content=content, vector=vector, type="async_test")
    assert len(await async_collection) == 1

    retrieved = await async_collection.get_by_id(entry_id)
    assert retrieved is not None
    assert retrieved["content"] == content
    # By default get_by_id in collection.py excludes vector if not in select_columns
    assert "vector" not in retrieved 

    retrieved_with_vec = await async_collection.get_by_id(entry_id, select_columns=["id", "vector"])
    assert "vector" in retrieved_with_vec and retrieved_with_vec["vector"] == vector

@pytest.mark.asyncio
async def test_async_collection_query(async_collection: AsyncAgentMemoryCollection, get_embedding_vec):
    content1 = "Relevant async content"
    content2 = "Irrelevant async stuff"
    await async_collection.add(content=content1, vector=get_embedding_vec(content1), type="relevant")
    await async_collection.add(content=content2, vector=get_embedding_vec(content2), type="irrelevant")

    results = await async_collection.query(
        query_text="Find relevant async data", # EF will embed this
        k=1,
        filter_sql="type = 'relevant'"
    )
    assert len(results) == 1
    assert results[0]["content"] == content1

@pytest.mark.asyncio
async def test_async_collection_delete(async_collection: AsyncAgentMemoryCollection):
    entry_id = await async_collection.add(content="To delete async", type="temp_async")
    assert len(await async_collection) == 1
    
    deleted_count = await async_collection.delete(entry_id=entry_id)
    assert deleted_count == 1
    assert len(await async_collection) == 0
    assert await async_collection.get_by_id(entry_id) is None

@pytest.mark.asyncio
async def test_async_collection_count(async_collection: AsyncAgentMemoryCollection):
    assert await async_collection.count() == 0
    await async_collection.add_batch([
        {"content": "ac1", "type": "X"},
        {"content": "ac2", "type": "Y"},
    ]) # EF handles vectors
    assert await async_collection.count() == 2
    assert await async_collection.count(filter_sql="type = 'X'") == 1

@pytest.mark.asyncio
async def test_async_collection_prune(async_collection_ts_update: AsyncAgentMemoryCollection):
    # Use the _ts_update fixture for prune tests that rely on last_accessed
    coll = async_collection_ts_update
    now = time.time()
    await coll.add(content="Old async prune item", timestamp_created=now - 86400*5, importance_score=0.1)
    await coll.add(content="Newer async item", timestamp_created=now - 3600, importance_score=0.9)
    assert len(await coll) == 2

    pruned_count = await coll.prune_memories(min_importance_score=0.2) # Should prune the first one
    assert pruned_count == 1
    assert len(await coll) == 1