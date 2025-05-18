import pytest
import uuid
import time
import os
from typing import List, Dict, Tuple

from agentvector import AgentMemory, AsyncAgentMemory
from agentvector.exceptions import InitializationError, SchemaError, QueryError, OperationError, EmbeddingError
from agentvector.schemas import MemoryEntrySchema # Assuming MemoryEntrySchema is the base
from .conftest import VECTOR_DIMENSION_TEST, MyCustomTestSchema # Import from conftest

# Helper to generate multiple unique vectors for testing distinctness
def generate_distinct_vectors(count: int, ef_generate_func) -> List[List[float]]:
    return ef_generate_func([f"text_{i}" for i in range(count)])


# === Initialization Tests ===
def test_initialization_basic(agent_memory_instance: AgentMemory):
    """Test basic initialization and table creation."""
    assert agent_memory_instance.table is not None
    assert agent_memory_instance.table_name in agent_memory_instance.db.table_names()
    assert len(agent_memory_instance) == 0 # Should be empty

def test_initialization_recreate_table(test_db_path, test_embedding_function):
    """Test that recreate_table=True works."""
    table_name = "recreate_test"
    mem1 = AgentMemory(test_db_path, table_name, embedding_function=test_embedding_function, recreate_table=False)
    mem1.add(content="first entry")
    assert len(mem1) == 1

    mem2 = AgentMemory(test_db_path, table_name, embedding_function=test_embedding_function, recreate_table=True)
    assert len(mem2) == 0 # Table should have been recreated and empty

def test_initialization_with_custom_schema(test_db_path, test_embedding_function, custom_schema_type):
    table_name = "custom_schema_table"
    memory = AgentMemory(
        db_path=test_db_path,
        table_name=table_name,
        base_schema=custom_schema_type,
        embedding_function=test_embedding_function,
        recreate_table=True
    )
    assert memory.BaseSchema == custom_schema_type
    # Check if dynamic schema correctly includes custom fields
    assert "custom_field_string" in memory.DynamicSchema.model_fields
    
    # Test adding and retrieving with custom fields
    custom_val_str = "my custom value"
    custom_val_int = 123
    custom_val_list = ["item1", "item2"]
    entry_id = memory.add(
        content="Entry with custom schema fields",
        custom_field_string=custom_val_str,
        custom_field_int=custom_val_int,
        custom_field_list=custom_val_list
    )
    retrieved = memory.get_by_id(entry_id, select_columns=["id", "content", "custom_field_string", "custom_field_int", "custom_field_list"]) # Select custom fields
    assert retrieved is not None
    assert retrieved["custom_field_string"] == custom_val_str
    assert retrieved["custom_field_int"] == custom_val_int
    assert retrieved["custom_field_list"] == custom_val_list

def test_initialization_vector_dimension_conflict(test_db_path, test_embedding_function):
    with pytest.raises(InitializationError, match="conflicts with embedding_function's dimension"):
        AgentMemory(
            db_path=test_db_path, table_name="dim_conflict",
            embedding_function=test_embedding_function, # Has its own dimension (VECTOR_DIMENSION_TEST)
            vector_dimension=VECTOR_DIMENSION_TEST + 5 # Different dimension
        )

def test_initialization_no_dimension_info(test_db_path):
    with pytest.raises(InitializationError, match="vector_dimension must be provided if not using an embedding_function"):
        AgentMemory(db_path=test_db_path, table_name="no_dim_fail") # No EF, no vector_dimension


# === Add Operations Tests ===
def test_add_single_entry_with_ef(agent_memory_instance: AgentMemory):
    """Test adding a single entry where EF handles embedding."""
    content = "Test content for EF auto-embedding"
    entry_id = agent_memory_instance.add(content=content, type="ef_test")
    assert isinstance(entry_id, str)
    assert len(agent_memory_instance) == 1

    retrieved = agent_memory_instance.get_by_id(entry_id, select_columns=["id", "content", "type", "vector"])
    assert retrieved is not None
    assert retrieved["content"] == content
    assert retrieved["type"] == "ef_test"
    assert "vector" in retrieved and len(retrieved["vector"]) == VECTOR_DIMENSION_TEST

def test_add_single_entry_manual_vector(agent_memory_instance: AgentMemory, sample_vector):
    """Test adding a single entry with a manually provided vector."""
    content = "Content with manual vector"
    entry_id = agent_memory_instance.add(content=content, vector=sample_vector, type="manual_vec_test")
    assert len(agent_memory_instance) == 1
    retrieved = agent_memory_instance.get_by_id(entry_id, select_columns=["id", "content", "vector"])
    assert retrieved is not None
    assert retrieved["content"] == content
    assert retrieved["vector"] == sample_vector # Compare vector content

def test_add_vector_dimension_mismatch_manual(agent_memory_instance: AgentMemory):
    wrong_dim_vector = [0.1] * (VECTOR_DIMENSION_TEST + 1)
    with pytest.raises(SchemaError, match="Provided vector for ID .* has dimension"):
        agent_memory_instance.add(content="Dim mismatch", vector=wrong_dim_vector)

def test_add_missing_vector_and_ef_incapable(test_db_path):
    # EF that doesn't have source_column or content not provided for source_column
    class BadEF:
        def ndims(self): return VECTOR_DIMENSION_TEST
        # Missing source_column or generate method
    
    mem_no_ef_source = AgentMemory(test_db_path, "bad_ef_table", embedding_function=BadEF(), recreate_table=True)
    with pytest.raises(EmbeddingError, match="its source column .* not found in data"):
        mem_no_ef_source.add(type="some_type") # No content for EF, no vector

    mem_no_ef = AgentMemory(test_db_path, "no_ef_table_add", vector_dimension=VECTOR_DIMENSION_TEST, recreate_table=True)
    with pytest.raises(EmbeddingError, match="no 'vector' and no embedding_function is configured"):
        mem_no_ef.add(content="No vector here")


def test_add_batch_entries(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    vecs = generate_distinct_vectors(2, get_embedding_func_for_test)
    entries_data = [
        {"content": "Batch entry 1", "vector": vecs[0], "type": "batch_type_A"},
        {"content": "Batch entry 2 (no vector, use EF)", "type": "batch_type_B"},
    ]
    entry_ids = agent_memory_instance.add_batch(entries_data)
    assert len(entry_ids) == 2
    assert len(agent_memory_instance) == 2

    retrieved_1 = agent_memory_instance.get_by_id(entry_ids[0])
    assert retrieved_1["content"] == "Batch entry 1"
    retrieved_2 = agent_memory_instance.get_by_id(entry_ids[1])
    assert retrieved_2["content"] == "Batch entry 2 (no vector, use EF)"
    assert "vector" in retrieved_2 and retrieved_2["vector"] is not None


# === Query Tests ===
def test_query_basic_semantic_search(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    vecs = generate_distinct_vectors(3, get_embedding_func_for_test)
    # Content designed for EF to produce somewhat distinct vectors
    contents = ["apple fruit red", "orange fruit citrus", "banana fruit yellow"]
    agent_memory_instance.add(content=contents[0], vector=vecs[0])
    agent_memory_instance.add(content=contents[1], vector=vecs[1])
    agent_memory_instance.add(content=contents[2], vector=vecs[2])

    query_vec = get_embedding_func_for_test(["apple related concept"])[0]
    results = agent_memory_instance.query(query_vector=query_vec, k=1, include_vector=True)
    assert len(results) == 1
    assert results[0]["content"] == contents[0] # Expect "apple fruit red" to be closest
    assert "_distance" in results[0]

def test_query_with_text_and_ef(agent_memory_instance: AgentMemory):
    agent_memory_instance.add(content="Relevant document about AI agents.")
    agent_memory_instance.add(content="Irrelevant document about cooking pasta.")
    
    results = agent_memory_instance.query(query_text="AI agent capabilities", k=1)
    assert len(results) == 1
    assert results[0]["content"] == "Relevant document about AI agents."

def test_query_with_filters(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    vecs = generate_distinct_vectors(3, get_embedding_func_for_test)
    agent_memory_instance.add(content="Item A", vector=vecs[0], type="Type1", importance_score=0.8, tags=["tagA", "common"])
    agent_memory_instance.add(content="Item B", vector=vecs[1], type="Type2", importance_score=0.5, tags=["tagB", "common"])
    agent_memory_instance.add(content="Item C", vector=vecs[2], type="Type1", importance_score=0.9, tags=["tagC"])

    query_vec = get_embedding_func_for_test(["Generic query"])[0]
    
    # Filter by type
    results_type = agent_memory_instance.query(query_vector=query_vec, k=2, filters={"type": "Type1"})
    assert len(results_type) == 2
    assert all(r["type"] == "Type1" for r in results_type)

    # Filter by importance
    results_importance = agent_memory_instance.query(query_vector=query_vec, k=1, filters={"importance_score": {"$gte": 0.85}})
    assert len(results_importance) == 1
    assert results_importance[0]["content"] == "Item C"

    # Filter by tag contains
    results_tag = agent_memory_instance.query(query_vector=query_vec, k=2, filters={"tags": {"$contains": "common"}})
    assert len(results_tag) == 2
    assert any(r["content"] == "Item A" for r in results_tag)
    assert any(r["content"] == "Item B" for r in results_tag)

    # Complex filter: (Type1 AND score > 0.85) OR (tags has common AND type is Type2)
    complex_filter = {
        "$or": [
            {"$and": [{"type": "Type1"}, {"importance_score": {"$gt": 0.85}}]}, # Item C
            {"$and": [{"tags": {"$contains": "common"}}, {"type": "Type2"}]}   # Item B
        ]
    }
    results_complex = agent_memory_instance.query(query_vector=query_vec, k=2, filters=complex_filter)
    assert len(results_complex) == 2
    contents_complex = {r["content"] for r in results_complex}
    assert "Item B" in contents_complex and "Item C" in contents_complex

def test_query_select_columns_and_vector_inclusion(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    vec = get_embedding_func_for_test(["Select test"])[0]
    agent_memory_instance.add(content="Test selection", vector=vec, type="sel_type", source="sel_source")

    # Select specific columns, exclude vector by default if not specified
    results = agent_memory_instance.query(query_vector=vec, k=1, select_columns=["id", "content", "type"])
    assert "id" in results[0] and "content" in results[0] and "type" in results[0]
    assert "source" not in results[0] and "vector" not in results[0]

    # Include vector explicitly
    results_incl_vec = agent_memory_instance.query(query_vector=vec, k=1, include_vector=True)
    assert "vector" in results_incl_vec[0]

    # Select columns including vector
    results_sel_vec = agent_memory_instance.query(query_vector=vec, k=1, select_columns=["content", "vector"])
    assert "content" in results_sel_vec[0] and "vector" in results_sel_vec[0]
    assert "id" not in results_sel_vec[0] # id is not in select_columns

def test_query_empty_results(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    query_vec = get_embedding_func_for_test(["Non existent query"])[0]
    results = agent_memory_instance.query(query_vector=query_vec, k=1)
    assert len(results) == 0

    # Query with filter that matches nothing
    agent_memory_instance.add(content="Exists", vector=get_embedding_func_for_test(["Exists"])[0], type="RealType")
    results_filter_none = agent_memory_instance.query(query_text="Exists", k=1, filters={"type": "FakeType"})
    assert len(results_filter_none) == 0


# === Timestamp Last Accessed Tests ===
def test_timestamp_last_accessed_on_query(agent_memory_instance_ts_update: AgentMemory, get_embedding_func_for_test):
    memory = agent_memory_instance_ts_update # This instance has update_last_accessed_on_query=True
    content = "Test timestamp update on query"
    vec = get_embedding_func_for_test([content])[0]
    entry_id = memory.add(content=content, vector=vec, timestamp_last_accessed=None) # Explicitly None

    initial_entry = memory.get_by_id(entry_id, select_columns=["id", "timestamp_last_accessed"])
    # get_by_id in ts_update instance also updates timestamp
    assert initial_entry is not None
    original_ts_accessed = initial_entry.get("timestamp_last_accessed")
    assert original_ts_accessed is not None # Should be updated by get_by_id

    time.sleep(0.01) # Ensure time progresses enough for a different timestamp

    _ = memory.query(query_vector=vec, k=1) # Perform a query that should retrieve the entry
    
    updated_entry = memory.get_by_id(entry_id, select_columns=["id", "timestamp_last_accessed"])
    assert updated_entry is not None
    new_ts_accessed = updated_entry.get("timestamp_last_accessed")
    assert new_ts_accessed is not None
    assert new_ts_accessed > original_ts_accessed

def test_timestamp_last_accessed_on_get_by_id(agent_memory_instance_ts_update: AgentMemory, get_embedding_func_for_test):
    memory = agent_memory_instance_ts_update
    entry_id = memory.add(content="Test get_by_id timestamp", vector=get_embedding_func_for_test(["ts test"])[0], timestamp_last_accessed=None)
    
    entry_before_get = memory.table.search().where(f"id = '{entry_id}'").limit(1).to_df().to_dict('records')[0]
    assert entry_before_get.get("timestamp_last_accessed") is None

    time.sleep(0.01)
    retrieved_entry = memory.get_by_id(entry_id) # This should update the timestamp
    assert retrieved_entry is not None
    assert retrieved_entry.get("timestamp_last_accessed") is not None
    
    entry_after_get = memory.table.search().where(f"id = '{entry_id}'").limit(1).to_df().to_dict('records')[0]
    assert entry_after_get.get("timestamp_last_accessed") is not None
    assert entry_after_get.get("timestamp_last_accessed") == retrieved_entry.get("timestamp_last_accessed")


# === Get/Delete/Count Tests ===
def test_get_by_id_found_not_found(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    entry_id = agent_memory_instance.add(content="Test get_by_id", vector=get_embedding_func_for_test(["get test"])[0])
    retrieved = agent_memory_instance.get_by_id(entry_id)
    assert retrieved is not None and retrieved["id"] == entry_id
    
    non_existent_id = str(uuid.uuid4())
    assert agent_memory_instance.get_by_id(non_existent_id) is None

def test_delete_by_id(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    entry_id = agent_memory_instance.add(content="To be deleted", vector=get_embedding_func_for_test(["delete me"])[0])
    assert len(agent_memory_instance) == 1
    
    deleted_count = agent_memory_instance.delete(entry_id=entry_id)
    assert deleted_count == 1 # Matched 1 item
    assert len(agent_memory_instance) == 0
    assert agent_memory_instance.get_by_id(entry_id) is None

def test_delete_by_filter(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    agent_memory_instance.add(content="Delete type A", vector=get_embedding_func_for_test(["del A"])[0], type="TypeA")
    agent_memory_instance.add(content="Keep type B", vector=get_embedding_func_for_test(["keep B"])[0], type="TypeB")
    agent_memory_instance.add(content="Another Delete type A", vector=get_embedding_func_for_test(["del A2"])[0], type="TypeA")
    assert len(agent_memory_instance) == 3

    deleted_count = agent_memory_instance.delete(filter_sql="type = 'TypeA'")
    assert deleted_count == 2 # Matched 2 items
    assert len(agent_memory_instance) == 1
    remaining = agent_memory_instance.query(query_text="anything", k=1)[0] # Crude get first
    assert remaining["type"] == "TypeB"

def test_delete_no_match(agent_memory_instance: AgentMemory):
    deleted_count = agent_memory_instance.delete(filter_sql="type = 'NonExistentType'")
    assert deleted_count == 0

def test_count_entries(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    assert agent_memory_instance.count() == 0
    agent_memory_instance.add_batch([
        {"content": "c1", "vector": get_embedding_func_for_test(["c1"])[0], "type": "X"},
        {"content": "c2", "vector": get_embedding_func_for_test(["c2"])[0], "type": "Y"},
        {"content": "c3", "vector": get_embedding_func_for_test(["c3"])[0], "type": "X", "importance_score": 0.9},
    ])
    assert agent_memory_instance.count() == 3
    assert len(agent_memory_instance) == 3 # Test __len__

    assert agent_memory_instance.count(filters={"type": "X"}) == 2
    assert agent_memory_instance.count(filter_sql="type = 'Y'") == 1
    assert agent_memory_instance.count(filters={"importance_score": {"$gte": 0.5}}) == 1


# === Cognitive Functions Tests ===
def test_prune_memories(agent_memory_instance_ts_update: AgentMemory, get_embedding_func_for_test):
    mem = agent_memory_instance_ts_update # Uses TS update instance for last_accessed tests
    now = time.time()
    vecs = generate_distinct_vectors(4, get_embedding_func_for_test)

    # Entry 1: Old, low importance, not accessed recently
    mem.add(content="Prune Candidate 1", vector=vecs[0], timestamp_created=now - 86400*30, timestamp_last_accessed=now - 86400*20, importance_score=0.1)
    # Entry 2: Recent, but very low importance
    mem.add(content="Prune Candidate 2", vector=vecs[1], timestamp_created=now - 86400*1, timestamp_last_accessed=now - 86400*1, importance_score=0.05)
    # Entry 3: Old, but high importance
    mem.add(content="Keep Candidate 1", vector=vecs[2], timestamp_created=now - 86400*30, timestamp_last_accessed=now-86400*1, importance_score=0.9)
    # Entry 4: Recent, accessed recently, medium importance
    mem.add(content="Keep Candidate 2", vector=vecs[3], timestamp_created=now - 86400*5, timestamp_last_accessed=now - 3600, importance_score=0.6)
    
    assert len(mem) == 4

    # Dry run first: Prune if (older than 15 days AND importance < 0.5) OR (last_accessed > 10 days ago)
    # Candidate 1: Meets (old AND imp<0.5). Meets (last_accessed > 10d). -> PRUNE
    # Candidate 2: Not old. Imp < 0.5, but not part of an AND with age. Not stale accessed. -> KEEP by this specific compound filter
    # A simpler filter might get it, e.g., just importance_score < 0.1
    
    # Let's test simple prune by importance_score < 0.08 (should get C2)
    pruned_dry = mem.prune_memories(min_importance_score=0.08, dry_run=True)
    assert pruned_dry == 1 # Candidate 2
    assert len(mem) == 4 # Dry run

    pruned_actual_imp = mem.prune_memories(min_importance_score=0.08, dry_run=False)
    assert pruned_actual_imp == 1
    assert len(mem) == 3 # Candidate 2 is gone

    # Now prune Candidate 1: older than 25 days AND importance < 0.2
    pruned_actual_c1 = mem.prune_memories(max_age_seconds=86400*25, min_importance_score=0.2, filter_logic="AND", dry_run=False)
    assert pruned_actual_c1 == 1 # Candidate 1
    assert len(mem) == 2

    # Ensure Keep Candidate 1 and Keep Candidate 2 are still there
    kept_contents = {r["content"] for r in mem.query(query_text="anything", k=2)}
    assert "Keep Candidate 1" in kept_contents
    assert "Keep Candidate 2" in kept_contents


def mock_summarization_callback(memories: List[Dict], topic: str) -> Tuple[str, List[float]]:
    summary_content = f"Summary of {len(memories)} items on '{topic}'."
    # Use a fixed vector for test predictability or use a passed-in EF
    # For now, assume global test_embedding_function fixture can be accessed or mock it.
    # This part is tricky for a generic test. Let's assume EF is implicitly available via AgentMemory's config.
    # For simplicity, this mock won't generate a real embedding for this test.
    # In real reflect_and_summarize, the vector comes from the AgentMemory's EF or is passed.
    # Here, the test needs to ensure the vector is compatible.
    # Let's create a dummy vector of correct dimension.
    dummy_summary_vector = [0.01] * VECTOR_DIMENSION_TEST 
    return summary_content, dummy_summary_vector

def test_reflect_and_summarize(agent_memory_instance: AgentMemory, get_embedding_func_for_test):
    mem = agent_memory_instance
    vecs = generate_distinct_vectors(3, get_embedding_func_for_test)
    mem.add(content="Fact A about topic Alpha", vector=vecs[0], tags=["alpha"])
    mem.add(content="Fact B concerning Alpha topic", vector=vecs[1], tags=["alpha"])
    mem.add(content="Fact C unrelated to Alpha", vector=vecs[2], tags=["beta"])
    
    initial_count = len(mem)

    # Define a summarization callback that uses the memory's configured EF if possible, or a test EF
    def test_summary_cb(retrieved_memories: List[Dict], topic: str) -> Tuple[str, List[float]]:
        summary_text = f"Test summary for {topic} based on {len(retrieved_memories)} items."
        # Use the get_embedding_func_for_test fixture from conftest
        summary_vector = get_embedding_func_for_test([summary_text])[0]
        return summary_text, summary_vector


    summary_id = mem.reflect_and_summarize(
        query_text="Alpha topic", # Will be embedded by AgentMemory's EF
        summarization_callback=test_summary_cb,
        k_to_retrieve=2,
        query_filters={"tags": {"$contains": "alpha"}},
        new_memory_type="summary_alpha",
        delete_original_memories=False
    )
    assert summary_id is not None
    assert len(mem) == initial_count + 1 # One new summary memory

    summary_entry = mem.get_by_id(summary_id, select_columns=["id", "content", "type", "related_memories", "vector"])
    assert summary_entry is not None
    assert summary_entry["type"] == "summary_alpha"
    assert len(summary_entry["related_memories"]) == 2 # Should relate to the 2 alpha facts
    assert "vector" in summary_entry and len(summary_entry["vector"]) == VECTOR_DIMENSION_TEST

    # Test with delete_original_memories = True
    summary_id_delete = mem.reflect_and_summarize(
        query_text="Alpha topic again",
        summarization_callback=test_summary_cb,
        k_to_retrieve=2, # This will now retrieve the previous summary and one original fact if k=2
        query_filters={"tags": {"$contains": "alpha"}}, # This filter is on original, not the new summary type
        new_memory_type="summary_alpha_v2",
        delete_original_memories=True
    )
    assert summary_id_delete is not None
    # Expected count: (initial_count + 1) - 2 (originals for summary) + 1 (new summary) = initial_count
    # This depends on what reflect_and_summarize queries and deletes.
    # If it queries including previous summaries of type "alpha", then it might delete them.
    # This needs careful thought on the query for reflect_and_summarize.
    # For now, let's assume it deletes the 2 original Alpha facts if they are retrieved again.
    # Current query for R&S does not exclude prior summaries.
    # So, if one original + one summary were retrieved, 2 would be deleted. Total count = (init_count+1) - 2 + 1 = init_count
    assert len(mem) == initial_count # initial 3 + 1st summary - 2 (retrieved for 2nd summary) + 2nd summary = 3

# === Async Tests (basic examples, more would be needed) ===
@pytest.mark.asyncio
async def test_async_add_and_query(async_agent_memory_instance: AsyncAgentMemory):
    mem = async_agent_memory_instance
    content = "Async test content"
    entry_id = await mem.add(content=content, type="async_type")
    assert len(await mem) == 1

    results = await mem.query(query_text=content, k=1, filters={"type": "async_type"})
    assert len(results) == 1
    assert results[0]["content"] == content

@pytest.mark.asyncio
async def test_async_prune_memories(async_agent_memory_instance: AsyncAgentMemory):
    mem = async_agent_memory_instance
    await mem.add(content="Old async item", timestamp_created=time.time() - 86400*5, importance_score=0.1)
    await mem.add(content="New async item", importance_score=0.9)
    assert len(await mem) == 2

    pruned_count = await mem.prune_memories(min_importance_score=0.2) # Should prune the old item
    assert pruned_count == 1
    assert len(await mem) == 1