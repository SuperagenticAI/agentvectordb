import asyncio
import time
import os
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentvector import AgentVectorStore, AsyncAgentVectorStore
from agentvector.embeddings import DefaultTextEmbeddingFunction

DB_DIR = "./_agentvector_mvp_quickstart_db"
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory): shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

def run_sync_part():
    print("--- Synchronous API Example ---")
    store = AgentVectorStore(db_path=DB_DIR)
    ep_mem = store.get_or_create_collection(
        name="ep_sync", embedding_function=ef, update_last_accessed_on_query=True, recreate=True
    )
    print(f"Sync Collection '{ep_mem.name}' ready. Entries: {len(ep_mem)}")
    ep_mem.add(content="Sync: User asked about collections.", type="user_q", tags=["sync_tag"])
    ep_mem.add(content="Sync: Agent decided to use collections.", type="agent_d", importance_score=0.7)
    
    results = ep_mem.query(query_text="sync collections", k=1, filter_sql="type = 'user_q'")
    for res in results: print(f"  Sync Query: '{res.get('content')}', Type: '{res.get('type')}'")

async def run_async_part():
    print("\n--- Asynchronous API Example ---")
    async_store = AsyncAgentVectorStore(db_path=DB_DIR)
    ag_thoughts = await async_store.get_or_create_collection(
        name="thoughts_async", embedding_function=ef, update_last_accessed_on_query=True, recreate=True
    )
    print(f"Async Collection '{ag_thoughts.name}' ready. Entries: {await ag_thoughts.count()}")
    await ag_thoughts.add(content="Async: Plan Project Nebula.", type="plan", metadata={"proj": "Nebula"})
    
    results_async = await ag_thoughts.query(query_text="Nebula plan", k=1, filter_sql="metadata.proj = 'Nebula'")
    for res in results_async: print(f"  Async Query: '{res.get('content')}', Meta: {res.get('metadata')}")

    print("\nCollections in store (async):")
    for name in await async_store.list_collections(): print(f"  - {name}")

if __name__ == "__main__":
    cleanup_db_dir(DB_DIR)
    run_sync_part()
    asyncio.run(run_async_part())
    print("\nQuick Start example finished.")