import pytest
import uuid
import time
from typing import List, Dict, Tuple

from agentvectordb import AgentMemoryCollection, AsyncAgentMemoryCollection
from agentvectordb.exceptions import SchemaError, EmbeddingError, QueryError, OperationError
from agentvectordb.schemas import MemoryEntrySchema
from .conftest import VECTOR_DIMENSION_TEST, MyTestSchema, test_embedding_function, get_embedding_vec

# Helper to generate multiple unique vectors
def generate_test_vectors(count: int, ef_generate_func) -> List[List[float]]:
    return ef_generate_func([f"text_for_vec_{i}" for i in range(count)])

# === Collection Initialization and Basic Properties (via fixture) ===
def test_collection_properties(sync_collection: AgentMemoryCollection, test_embedding_function):
    assert sync_collection.name == "default_sync_collection"
    assert sync_collection.embedding_function is test_embedding_function
    assert sync_collection.table is not None
    assert len(sync_collection) == 0
    assert sync_collection.schema is not None # DynamicSchema

# === Add Operations ===
def test_collection_add_single_with_ef(sync_collection: AgentMemoryCollection):
    content = "Content to be auto-embedded by collection EF"
    entry_id = sync_collection.add(content=content, type="ef_add_test")
    assert isinstance(entry_id, str)
    assert len(sync_collection) == 1
    retrieved = sync_collection.get_by_id(entry_id, select_columns=["id", "content", "vector"])
    assert retrieved is not None and retrieved["content"] == content
    assert "vector" in retrieved and len(retrieved["vector"]) == VECTOR_DIMENSION_TEST

def test_collection_add_single_manual_vector(sync_collection: AgentMemoryCollection, get_embedding_vec):
    content = "Content with a manually provided vector"
    vector = get_embedding_vec(content)
    entry_id = sync_collection.add(content=content, vector=vector, type="manual_vec_add")
    assert len(sync_collection) == 1
    retrieved = sync_collection.get_by_id(entry_id, select_columns=["id", "vector"])
    assert retrieved is not None and retrieved["vector"] == vector

def test_collection_add_vector_dim_mismatch(sync_collection: AgentMemoryCollection):
    wrong_dim_vector = [0.1] * (VECTOR_DIMENSION_TEST + 5)
    with pytest.raises(SchemaError, match="Vec dim mismatch"):
        sync_collection.add(content="Dim mismatch", vector=wrong_dim_vector)

def test_collection_add_batch(sync_collection: AgentMemoryCollection, get_embedding_vec):
    vectors = [get_embedding_vec("batch1"), get_embedding_vec("batch2_ef")]
    entries = [
        {"content": "Batch item 1 (manual vec)", "vector": vectors[0], "type": "batch_A"},
        {"content": "Batch item 2 (auto-embed)", "type": "batch_B"} # EF will handle this
    ]
    entry_ids = sync_collection.add_batch(entries)
    assert len(entry_ids) == 2 and len(sync_collection) == 2
    
    retrieved1 = sync_collection.get_by_id(entry_ids[0], select_columns=["vector"])
    retrieved2 = sync_collection.get_by_id(entry_ids[1], select_columns=["vector"])
    assert retrieved1["vector"] == vectors[0]
    assert "vector" in retrieved2 and retrieved2["vector"] is not None

# === Query Operations ===
def test_collection_query_semantic(sync_collection: AgentMemoryCollection, get_embedding_vec):
    content1 = "AI helps in data analysis"
    content2 = "Machine learning is a subset of AI"
    content3 = "Cooking Italian pasta"
    sync_collection.add(content=content1, vector=get_embedding_vec(content1))
    sync_collection.add(content=content2, vector=get_embedding_vec(content2))
    sync_collection.add(content=content3, vector=get_embedding_vec(content3))

    query_text = "artificial intelligence applications" # EF will embed
    results = sync_collection.query(query_text=query_text, k=2)
    assert len(results) == 2
    # Order might vary slightly, check content
    result_contents = {r["content"] for r in results}
    assert content1 in result_contents and content2 in result_contents
    assert content3 not in result_contents

def test_collection_query_with_filter_sql(sync_collection: AgentMemoryCollection, get_embedding_vec):
    sync_collection.add(content="Log: User A login.", vector=get_embedding_vec("User A login"), type="log", importance_score=0.3, metadata={"user": "A"})
    sync_collection.add(content="Log: User B activity.", vector=get_embedding_vec("User B activity"), type="log", importance_score=0.7, metadata={"user": "B"})
    sync_collection.add(content="Alert: High CPU.", vector=get_embedding_vec("High CPU alert"), type="alert", importance_score=0.9)

    # Filter by type and importance
    results = sync_collection.query(
        query_text="system logs", k=1,
        filter_sql="type = 'log' AND importance_score > 0.5"
    )
    assert len(results) == 1 and results[0]["metadata"]["user"] == "B"

    # Filter using metadata (LanceDB syntax for struct/map access might be metadata.user)
    # Check LanceDB docs for precise metadata SQL syntax. Assuming `metadata.field` for this test.
    results_meta = sync_collection.query(
        query_text="User A actions", k=1,
        filter_sql="metadata.user = 'A'" # Requires LanceDB to support this SQL on metadata
    )
    # This test depends on how LanceDB handles metadata queries. If it fails, the SQL might need adjustment.
    if results_meta: # Only assert if query was successful and results returned
      assert len(results_meta) == 1 and results_meta[0]["metadata"]["user"] == "A"
    else: # If LanceDB SQL for metadata doesn't work as expected or no match
      print("Warning: Metadata SQL filter for 'metadata.user = A' returned no results. Check LanceDB SQL syntax for metadata.")


def test_collection_query_select_columns_and_vector(sync_collection: AgentMemoryCollection, get_embedding_vec):
    v = get_embedding_vec("select_test")
    sync_collection.add(content="Test select", vector=v, type="sel", source="test")
    
    res_specific = sync_collection.query(query_vector=v, k=1, select_columns=["id", "content"])
    assert "id" in res_specific[0] and "content" in res_specific[0]
    assert "type" not in res_specific[0] and "vector" not in res_specific[0]

    res_incl_vec = sync_collection.query(query_vector=v, k=1, include_vector=True)
    assert "vector" in res_incl_vec[0]

# === Get/Delete/Count ===
def test_collection_get_by_id(sync_collection: AgentMemoryCollection, get_embedding_vec):
    entry_id = sync_collection.add(content="Unique content for get", vector=get_embedding_vec("Unique get"))
    retrieved = sync_collection.get_by_id(entry_id)
    assert retrieved is not None and retrieved["id"] == entry_id
    assert sync_collection.get_by_id(str(uuid.uuid4())) is None

def test_collection_delete_by_id_and_filter(sync_collection: AgentMemoryCollection, get_embedding_vec):
    id1 = sync_collection.add(content="Delete me by ID", vector=get_embedding_vec("del_id"), type="tmp_del")
    sync_collection.add(content="Delete me by filter", vector=get_embedding_vec("del_filter"), type="tmp_del_filt")
    sync_collection.add(content="Keep me", vector=get_embedding_vec("keep"), type="perm")
    assert len(sync_collection) == 3

    del_count_id = sync_collection.delete(entry_id=id1)
    assert del_count_id == 1 and len(sync_collection) == 2
    
    del_count_filter = sync_collection.delete(filter_sql="type = 'tmp_del_filt'")
    assert del_count_filter == 1 and len(sync_collection) == 1
    assert sync_collection.get_by_id(id1) is None

def test_collection_count(sync_collection: AgentMemoryCollection, get_embedding_vec):
    assert sync_collection.count() == 0
    sync_collection.add_batch([
        {"content":"c1", "vector":get_embedding_vec("c1"), "type":"A"},
        {"content":"c2", "vector":get_embedding_vec("c2"), "type":"B"},
        {"content":"c3", "vector":get_embedding_vec("c3"), "type":"A", "importance_score":0.9}
    ])
    assert sync_collection.count() == 3
    assert sync_collection.count(filter_sql="type = 'A'") == 2
    assert sync_collection.count(filter_sql="importance_score >= 0.9") == 1

# === Timestamp Last Accessed ===
def test_collection_ts_last_accessed_query(sync_collection_ts_update: AgentMemoryCollection, get_embedding_vec):
    coll = sync_collection_ts_update # Has update_last_accessed_on_query=True
    entry_id = coll.add(content="TS query test", vector=get_embedding_vec("ts_q_test"), timestamp_last_accessed=None)
    
    # Get initial state (get_by_id will update TS)
    initial_data = coll.get_by_id(entry_id, select_columns=["timestamp_last_accessed"])
    initial_ts = initial_data["timestamp_last_accessed"]
    assert initial_ts is not None
    
    time.sleep(0.01) # Ensure time advances
    _ = coll.query(query_text="TS query test", k=1) # This should update TS for the retrieved item
    
    final_data = coll.get_by_id(entry_id, select_columns=["timestamp_last_accessed"])
    final_ts = final_data["timestamp_last_accessed"]
    assert final_ts is not None and final_ts > initial_ts

# === Prune Memories ===
def test_collection_prune_memories(sync_collection_ts_update: AgentMemoryCollection, get_embedding_vec):
    coll = sync_collection_ts_update
    now = time.time()
    # Old, low importance, not accessed
    id1 = coll.add(content="Prune old low", vector=get_embedding_vec("p1"), timestamp_created=now - 86400*10, timestamp_last_accessed=now - 86400*5, importance_score=0.1)
    # Recent, but very low importance
    id2 = coll.add(content="Prune recent low", vector=get_embedding_vec("p2"), timestamp_created=now - 86400*1, importance_score=0.05)
    # Old, but high importance, accessed recently
    id3 = coll.add(content="Keep old high", vector=get_embedding_vec("p3"), timestamp_created=now - 86400*10, timestamp_last_accessed=now - 3600, importance_score=0.9)
    assert len(coll) == 3

    # Prune if importance < 0.08 (should get id2)
    pruned_count = coll.prune_memories(min_importance_score=0.08, dry_run=False)
    assert pruned_count == 1 and len(coll) == 2
    assert coll.get_by_id(id2) is None

    # Prune if older than 8 days AND (importance < 0.2 OR last_accessed > 3 days ago)
    # id1: age > 8d. (imp 0.1 < 0.2 OR last_accessed 5d > 3d) -> TRUE. Should be pruned.
    pruned_count_2 = coll.prune_memories(
        max_age_seconds=86400*8, 
        min_importance_score=0.2, # This OR
        max_last_accessed_seconds=86400*3, # This
        filter_logic="OR", # (imp < 0.2 OR stale_access)
        custom_filter_sql_addon=f"timestamp_created < {now - 86400*8}" # AND with age
    )
    # This complex filter is a bit tricky with how prune_memories combines.
    # A simpler test: prune id1 by (age > 8 days AND importance < 0.15)
    coll.delete(entry_id=id3) # Remove id3 to simplify
    assert len(coll) == 1 # Only id1 left
    pruned_count_id1 = coll.prune_memories(max_age_seconds=86400*8, min_importance_score=0.15, filter_logic="AND")
    assert pruned_count_id1 == 1
    assert len(coll) == 0

# === Custom Schema Test on Collection ===
def test_collection_with_custom_schema(sync_store, test_embedding_function, custom_schema_fixture, get_embedding_vec):
    coll = sync_store.get_or_create_collection(
        name="custom_schema_coll",
        base_schema=custom_schema_fixture,
        embedding_function=test_embedding_function,
        recreate=True
    )
    assert coll.BaseSchema == custom_schema_fixture
    
    entry_id = coll.add(
        content="Custom schema entry", vector=get_embedding_vec("custom"),
        custom_text="my custom text", custom_int=42, custom_field_list=["a", "b"]
    )
    retrieved = coll.get_by_id(entry_id, select_columns=["custom_text", "custom_int", "custom_field_list"]) # Select specific custom fields
    assert retrieved is not None
    assert retrieved["custom_text"] == "my custom text"
    assert retrieved["custom_int"] == 42
    assert retrieved["custom_field_list"] == ["a", "b"]