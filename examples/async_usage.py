import asyncio
import time
import os
import shutil
import sys

# Ensure agentvector is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentvector import AgentMemory, AsyncAgentMemory
from agentvector.embeddings import DefaultTextEmbeddingFunction

# --- Configuration ---
DB_DIR_ASYNC = "./_agentvector_async_db"
TABLE_NAME_ASYNC = "async_agent_stream"
ef_async = DefaultTextEmbeddingFunction(dimension=96) # Yet another dimension for variety
VECTOR_DIMENSION_ASYNC = ef_async.ndims()

def cleanup_async_db():
    if os.path.exists(DB_DIR_ASYNC):
        shutil.rmtree(DB_DIR_ASYNC)
    os.makedirs(DB_DIR_ASYNC, exist_ok=True)

async def main_async_operations():
    cleanup_async_db()
    print(f"--- Running AsyncAgentMemory Standalone Example ---")
    print(f"Using DB at: {DB_DIR_ASYNC}")

    # 1. Create the synchronous backend AgentMemory instance
    sync_backend = AgentMemory(
        db_path=DB_DIR_ASYNC,
        table_name=TABLE_NAME_ASYNC,
        embedding_function=ef_async,
        recreate_table=True, # Fresh start
        update_last_accessed_on_query=True
    )

    # 2. Wrap it with AsyncAgentMemory
    async_memory = AsyncAgentMemory(sync_backend)

    # --- Test Asynchronous Operations ---
    print("\nAdding entries asynchronously...")
    entry_id_1 = await async_memory.add(
        content="User reported a bug in the payment module.",
        type="bug_report",
        source="user_support_channel",
        importance_score=0.9,
        tags=["bug", "payment_module", "urgent"]
    )
    print(f"Added async entry 1: {entry_id_1}")

    entry_id_2 = await async_memory.add(
        content="Agent successfully resolved the payment module bug.",
        type="resolution_log",
        source="agent_action_tracker",
        importance_score=0.8,
        related_memories=[entry_id_1], # Link to the bug report
        tags=["bug_fix", "payment_module", "resolved"]
    )
    print(f"Added async entry 2: {entry_id_2}")

    print(f"Current count in async_memory: {await async_memory.count()}")

    print("\nQuerying asynchronously for 'payment module issues':")
    query_results = await async_memory.query(
        query_text="payment module issues",
        k=2, # Expecting both entries
        filters={"tags": {"$contains": "payment_module"}}
    )
    print(f"Found {len(query_results)} results:")
    for res in query_results:
        print(f"  Content: '{res.get('content', '')[:60]}...' "
              f"Type: {res.get('type')}, Importance: {res.get('importance_score')}")
        # Check if timestamp_last_accessed was updated
        assert res.get('timestamp_last_accessed') is not None, "Timestamp_last_accessed should be updated"
        print(f"  Last Accessed: {time.ctime(res.get('timestamp_last_accessed', 0))}")


    print("\nGetting an entry by ID asynchronously:")
    retrieved_entry = await async_memory.get_by_id(entry_id_1)
    if retrieved_entry:
        print(f"Retrieved by ID '{entry_id_1[:8]}...': Content='{retrieved_entry.get('content', '')[:60]}...'")
        assert retrieved_entry.get('timestamp_last_accessed') is not None, "Timestamp_last_accessed should be updated by get_by_id"
    else:
        print(f"Could not retrieve entry with ID {entry_id_1}")


    print("\nTesting asynchronous deletion:")
    # Add a dummy entry to delete
    dummy_id = await async_memory.add(content="This is a temporary memory to be deleted.", type="temp")
    print(f"Added dummy entry {dummy_id} for deletion test. Count: {await async_memory.count()}")
    
    delete_op_count = await async_memory.delete(entry_id=dummy_id) # Returns num_matching (1)
    print(f"Deletion operation for ID {dummy_id} attempted. Matched/deleted: {delete_op_count}.")
    
    # Verify deletion
    dummy_after_delete = await async_memory.get_by_id(dummy_id)
    assert dummy_after_delete is None, "Dummy entry should have been deleted"
    print(f"Confirmed dummy entry is deleted. Count now: {await async_memory.count()}")


    print("\n--- AsyncAgentMemory Standalone Example Finished ---")


if __name__ == "__main__":
    asyncio.run(main_async_operations())