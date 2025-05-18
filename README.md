# AgentVector 🧠

**AgentVector: The Cognitive Core for Your AI Agents.**

AgentVector is a lightweight, embeddable vector database specifically designed for Agentic AI systems. It empowers individual agents with persistent memory, semantic search capabilities, and tools for internal reasoning and learning. Built on the performance and simplicity of [LanceDB](https://github.com/lancedb/lancedb), AgentVector aims to be the default memory layer for sophisticated AI agents, offering a familiar "collection-based" API.

## Why AgentVector?

*   **Familiar API:** Uses a `Store -> Collection` model, similar to other popular vector databases, for ease of adoption.
*   **Lightweight & Embeddable:** Runs directly within your agent's process using LanceDB. No separate server, minimal dependencies.
*   **Agent-Centric Schema:** Default schema includes fields like `type` (observation, thought, goal), `source`, `importance_score`, and `timestamp_last_accessed` to provide a cognitive framework for each memory entry within a collection.
*   **Temporal Dynamics:** Built-in support for recency, mechanisms for memory decay (`prune_memories` on a collection), and tracking when memories were last accessed.
*   **Rich Querying:** Powerful semantic search combined with raw SQL filtering (`filter_sql`) for maximum flexibility on metadata.
*   **Seamless Embedding Integration:** Works with [LanceDB's embedding functions](https://lancedb.github.io/lancedb/embeddings/) or your custom embedding models, configurable per collection.
*   **Asynchronous API:** Provides `AsyncAgentVectorStore` and `AsyncAgentMemoryCollection` for integration with async-first agent frameworks.
*   **Open Source & Extensible:** Built with best practices, ready for community contributions.

## Core Features

*   **`AgentVectorStore`:** Manages the database file and provides access to multiple `AgentMemoryCollection` instances.
*   **`AgentMemoryCollection`:** Represents a distinct set of memories (a LanceDB table) with its own schema and configuration.
    *   **Persistent Storage:** File-based storage.
    *   **Vector Search:** Efficient ANN search.
    *   **Metadata Filtering:** Use `filter_sql` for powerful filtering.
    *   **CRUD Operations:** Add, retrieve, (implicitly) update `timestamp_last_accessed`, and delete memories.
    *   **Batch Operations:** Efficiently add multiple memories.
    *   **Memory Pruning:** `prune_memories` method for memory decay strategies.
*   **Dynamic Schema:** Flexible Pydantic-based schemas per collection.
*   **Timestamp Tracking:** Automatic `timestamp_created` and optional `timestamp_last_accessed` updates.
*   **Async Support:** Fully asynchronous API available.

## Installation

```bash
pip install agentvector
```

Or for the latest development version (once published):
```bash
pip install git+https://github.com/superagenticai/agentvector.git
```

To install locally for development:
```bash
git clone https://github.com/superagenticai/agentvector.git
cd agentvector
pip install -e .[dev]
```

## Quick Start

```python
import asyncio
import time
import os
import shutil
from agentvector import AgentVectorStore, AsyncAgentVectorStore, MemoryEntrySchema
from agentvector.embeddings import DefaultTextEmbeddingFunction # Example embedding function

# --- Configuration ---
DB_DIR = "./_agentvector_mvp_quickstart_db"
# Example embedding function (replace with a real one for production)
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory):
        shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

cleanup_db_dir(DB_DIR) # Clean slate for example

# === Synchronous API ===
print("--- Using Synchronous AgentVectorStore & AgentMemoryCollection ---")
# 1. Initialize the Store
store = AgentVectorStore(db_path=DB_DIR)

# 2. Get or create a Collection for episodic memories
episodic_memories = store.get_or_create_collection(
    name="episodic_stream",
    embedding_function=ef,
    # vector_dimension not strictly needed if ef defines it
    # base_schema=MyCustomEpisodicSchema, # Optional custom schema
    update_last_accessed_on_query=True,
    recreate=True # Ensure fresh for example
)
print(f"Collection '{episodic_memories.name}' ready. Total entries: {len(episodic_memories)}")

# 3. Add memories to the collection
episodic_memories.add(
    content="User inquired about AgentVector's collection feature.",
    type="user_interaction",
    source="chat_interface",
    tags=["agentvector_feature", "collections_api"]
)
episodic_memories.add(
    content="Agent decided to use the 'episodic_stream' collection for observations.",
    type="internal_decision",
    source="agent_reasoner",
    importance_score=0.7
)

# 4. Query the collection
print("\nQuerying 'episodic_stream' for 'collection feature':")
query_results = episodic_memories.query(
    query_text="AgentVector collection feature", # EF will embed this
    k=1,
    filter_sql="type = 'user_interaction'" # Raw SQL filter
)
for res in query_results:
    print(f"  Sync Query Result: Content='{res.get('content', 'N/A')}', Type='{res.get('type')}'")

# === Asynchronous API ===
print("\n--- Using Asynchronous AsyncAgentVectorStore & AsyncAgentMemoryCollection ---")
async def async_example_main():
    # 1. Initialize the Async Store
    async_store = AsyncAgentVectorStore(db_path=DB_DIR) # Can point to the same DB dir

    # 2. Get or create an Async Collection for agent thoughts
    agent_thoughts = await async_store.get_or_create_collection(
        name="agent_thoughts_log",
        embedding_function=ef,
        update_last_accessed_on_query=True,
        recreate=True # Ensure fresh for example
    )
    print(f"Async Collection '{agent_thoughts.name}' ready. Entries: {await agent_thoughts.count()}")

    # 3. Add memories asynchronously
    await agent_thoughts.add(
        content="Async thought: Need to plan next steps for Project Nebula.",
        type="planning_thought",
        importance_score=0.85,
        metadata={"project": "Nebula", "status": "pending_review"}
    )

    # 4. Query asynchronously
    print("\nQuerying 'agent_thoughts_log' for 'Project Nebula':")
    # Note: LanceDB SQL for metadata access is `metadata.field` or `metadata['field']`
    # Check LanceDB documentation for exact syntax for nested fields in SQL WHERE.
    # For simplicity, let's filter on a top-level field or assume flat metadata.
    # If metadata is `{"project": "Nebula"}` then `metadata['project']` or similar.
    # LanceDB 0.6+ syntax for struct access: `metadata.project = 'Nebula'`
    async_results = await agent_thoughts.query(
        query_text="Project Nebula planning",
        k=1,
        filter_sql="metadata.project = 'Nebula'" # LanceDB JSON/map access
    )
    for res in async_results:
        print(f"  Async Query Result: Content='{res.get('content', 'N/A')}', Importance='{res.get('importance_score')}'")

    # 5. List collections in the store
    print("\nCollections in the async store:")
    collections = await async_store.list_collections()
    for coll_name in collections:
        print(f"  - {coll_name}")
    
    # Cleanup a collection (example)
    # await async_store.delete_collection("agent_thoughts_log")
    # print(f"Deleted collection: agent_thoughts_log. Remaining: {await async_store.list_collections()}")


if __name__ == "__main__":
    asyncio.run(async_example_main()) # Combined sync part into async_example_main for simplicity
    print("\nQuick Start example finished.")
```

## API Overview

### `AgentVectorStore(db_path: str)`
*   `db_path`: Directory where LanceDB database files are stored.

*   **Methods:**
    *   `get_or_create_collection(name: str, embedding_function: Any, base_schema: Type[MemoryEntrySchema] = MemoryEntrySchema, vector_dimension: Optional[int] = None, update_last_accessed_on_query: bool = False, recreate: bool = False) -> AgentMemoryCollection`
    *   `get_collection(name: str) -> Optional[AgentMemoryCollection]` (Note: For MVP, primarily returns cached collections. Full rehydration of arbitrary existing tables is complex).
    *   `list_collections() -> List[str]`
    *   `delete_collection(name: str) -> bool`

### `AgentMemoryCollection` (Instance obtained from `AgentVectorStore`)
*   **Properties:**
    *   `name: str`
    *   `embedding_function: Any`
    *   `schema: Type[PydanticModel]` (The dynamic Pydantic schema used by the collection)
*   **Methods (MVP):**
    *   `add(**kwargs) -> str` (kwargs match `MemoryEntrySchema` fields)
    *   `add_batch(entries: List[Dict]) -> List[str]`
    *   `query(query_vector/query_text, k, filter_sql, select_columns, include_vector) -> List[Dict]`
    *   `get_by_id(entry_id: str, select_columns) -> Optional[Dict]`
    *   `delete(entry_id, filter_sql) -> int` (returns count of matched/attempted deletes)
    *   `count(filter_sql) -> int`
    *   `prune_memories(max_age_seconds, min_importance_score, max_last_accessed_seconds, filter_logic, custom_filter_sql_addon, dry_run) -> int`
    *   `__len__() -> int` (total items in collection)

### Asynchronous API
*   `AsyncAgentVectorStore(db_path: str)`
*   `AsyncAgentMemoryCollection`
    *   All methods of their synchronous counterparts are available as `async` methods.

## Detailed Usage (Examples)

*(Refer to Quick Start and future detailed example files for specific method calls)*

### Creating and Using Multiple Collections

```python
store = AgentVectorStore(db_path="./my_multi_agent_db")

# Collection for factual knowledge
kb_ef = DefaultTextEmbeddingFunction(dimension=128) # Specific EF for knowledge
knowledge_base = store.get_or_create_collection(
    name="knowledge_base",
    embedding_function=kb_ef,
    # base_schema=MyFactSchema # Optional custom schema for facts
)
knowledge_base.add(content="The Earth revolves around the Sun.", type="astronomy_fact")

# Collection for agent's own observations
obs_ef = DefaultTextEmbeddingFunction(dimension=96) # Different EF for observations
observations = store.get_or_create_collection(
    name="agent_observations",
    embedding_function=obs_ef,
    update_last_accessed_on_query=True
)
observations.add(content="Detected a sudden temperature drop.", type="sensor_reading", source="temp_sensor_alpha")

# Query across different collections by interacting with their respective objects
sun_facts = knowledge_base.query(query_text="Sun facts", k=1)
sensor_logs = observations.query(query_text="temperature readings", k=1)
```

### Filtering with `filter_sql`

`filter_sql` allows you to use LanceDB's full SQL filtering capabilities. Refer to [LanceDB SQL documentation](https://lancedb.github.io/lancedb/sql/) for syntax.

```python
# Assuming 'metadata' is a Dict field and 'importance_score' a float field in your schema
results = my_collection.query(
    query_text="relevant topic",
    k=5,
    filter_sql="type = 'log_entry' AND importance_score > 0.5 AND metadata.user_id = 'user123'"
)
```

### Memory Pruning

```python
# Prune memories in 'agent_observations' collection that are older than 7 days
# AND have an importance_score less than 0.3
seven_days_ago_seconds = 86400 * 7
pruned_count = observations.prune_memories(
    max_age_seconds=seven_days_ago_seconds,
    min_importance_score=0.3,
    filter_logic="AND", # Combine criteria with AND
    dry_run=False # Execute the prune
)
print(f"Pruned {pruned_count} old/unimportant observations.")
```

## Roadmap & Contributing

AgentVector is actively evolving. Future directions for `AgentMemoryCollection` include:
*   More sophisticated dictionary-based filter builder (in addition to `filter_sql`).
*   `reflect_and_summarize()` helper for cognitive reflection.
*   Support for LanceDB versioning and snapshots.
*   Schema evolution helpers.

Contributions are welcome! Please see `CONTRIBUTING.md` (to be created) for guidelines.

## License
This project is licensed under the Apache-2.0 License. (Or your chosen license)
