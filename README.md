# 🧠 AgentVectorDB

[![PyPI version](https://badge.fury.io/py/agentvectordb.svg)](https://badge.fury.io/py/agentvectordb)
[![Python versions](https://img.shields.io/pypi/pyversions/agentvectordb.svg)](https://pypi.org/project/agentvectordb/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://github.com/superagenticai/agentvectordb/workflows/Tests/badge.svg)](https://github.com/superagenticai/agentvectordb/actions)
[![Documentation](https://readthedocs.org/projects/agentvectordb/badge/?version=latest)](https://agentvectordb.readthedocs.io/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Coverage](https://codecov.io/gh/superagenticai/agentvectordb/branch/main/graph/badge.svg)](https://codecov.io/gh/superagenticai/agentvectordb)

**AgentVectorDB: The Cognitive Core for Your AI Agents**

AgentVectorDB is a lightweight, embeddable vector database designed for agentic AI systems. It empowers your agents with persistent memory, semantic search, and tools for internal reasoning and learning. Built on the performance and simplicity of [LanceDB](https://github.com/lancedb/lancedb), AgentVectorDB is the default memory layer for sophisticated AI agents, offering a familiar "collection-based" API.

---

## 🚀 Why AgentVectorDB?

- **Familiar API:** Uses a `Store -> Collection` model, similar to other popular vector databases.
- **Lightweight & Embeddable:** Runs directly within your agent's process using LanceDB. No separate server, minimal dependencies.
- **Agent-Centric Schema:** Default schema includes fields like `type` (observation, thought, goal), `source`, `importance_score`, and `last_accessed_at` to provide a cognitive framework for each memory entry.
- **Temporal Dynamics:** Built-in support for recency, memory decay (`prune_memories`), and tracking when memories were last accessed.
- **Rich Querying:** Powerful semantic search combined with SQL filtering (`filter_sql`) for maximum flexibility.
- **Seamless Embedding Integration:** Works with [LanceDB's embedding functions](https://lancedb.github.io/lancedb/embeddings/) or your custom embedding models, configurable per collection.
- **Asynchronous API:** Provides `AsyncAgentVectorDBStore` and `AsyncAgentMemoryCollection` for integration with async-first agent frameworks.
- **Open Source & Extensible:** Built with best practices, ready for community contributions.

---

## ✨ Features at a Glance

- **Persistent Storage:** File-based, no server required.
- **Vector Search:** Efficient ANN search.
- **Metadata Filtering:** Use `filter_sql` for powerful filtering.
- **CRUD Operations:** Add, retrieve, update, and delete memories.
- **Batch Operations:** Efficiently add multiple memories.
- **Memory Pruning:** `prune_memories` method for memory decay strategies.
- **Dynamic Schema:** Flexible Pydantic-based schemas per collection.
- **Timestamp Tracking:** Automatic `created_at` and optional `last_accessed_at` updates.
- **Async Support:** Fully asynchronous API available.

---

## 📦 Installation

```bash
pip install agentvectordb
```

Or for the latest development version:
```bash
pip install git+https://github.com/superagenticai/agentvectordb.git
```

To install locally for development:
```bash
git clone https://github.com/superagenticai/agentvectordb.git
cd agentvectordb
pip install -e .[dev]
```

---

## 🏁 Quickstart

```python
import asyncio
import os
import shutil
from agentvectordb import AgentVectorDBStore, AsyncAgentVectorDBStore
from agentvectordb.embeddings import DefaultTextEmbeddingFunction

print("\033[1;36m")
print("🧠🚀 Welcome to AgentVectorDB Quickstart! 🚀🧠")
print("A lightweight, embeddable vector database for agentic AI systems, built on LanceDB.\n")
print("\033[0m")

DB_DIR = "./_agentvectordb_mvp_quickstart_db"
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory):
        shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

cleanup_db_dir(DB_DIR)

# --- Synchronous API ---
print("\033[1;34m🔹 [SYNC] Episodic Memory Demo\033[0m")
store = AgentVectorDBStore(db_path=DB_DIR)
episodic_memories = store.get_or_create_collection(
    name="episodic_stream",
    embedding_function=ef,
    update_last_accessed_on_query=True,
    recreate=True
)
episodic_memories.add(
    content="User inquired about AgentVectorDB's collection feature.",
    type="user_interaction",
    source="chat_interface",
    tags=["agentvectordb_feature", "collections_api"]
)
episodic_memories.add(
    content="Agent decided to use the 'episodic_stream' collection for observations.",
    type="internal_decision",
    source="agent_reasoner",
    importance_score=0.7
)
query_results = episodic_memories.query(
    query_text="AgentVectorDB collection feature",
    k=1,
    filter_sql="type = 'user_interaction'"
)
print("\033[1;32m\n🌟 Sync Query Results:\033[0m")
for res in query_results:
    print(f"\033[1;33m  • {res.get('content', 'N/A')} \033[0m\033[0;35m(Type: {res.get('type')})\033[0m")

# --- Asynchronous API ---
async def async_example_main():
    print("\n\033[1;34m🔹 [ASYNC] Agent Thoughts Log Demo\033[0m")
    async_store = AsyncAgentVectorDBStore(db_path=DB_DIR)
    agent_thoughts = await async_store.get_or_create_collection(
        name="agent_thoughts_log",
        embedding_function=ef,
        update_last_accessed_on_query=True,
        recreate=True
    )
    await agent_thoughts.add(
        content="Async thought: Need to plan next steps for Project Nebula.",
        type="planning_thought",
        importance_score=0.85,
        metadata={"project": "Nebula", "status": "pending_review"}
    )
    async_results = await agent_thoughts.query(
        query_text="Project Nebula planning",
        k=1,
        filter_sql="metadata.extra LIKE '%Nebula%'"
    )
    print("\033[1;32m\n🌟 Async Query Results:\033[0m")
    for res in async_results:
        print(f"\033[1;33m  • {res.get('content', 'N/A')} \033[0m\033[0;35m(Importance: {res.get('importance_score')})\033[0m")
    collections = await async_store.list_collections()
    print("\n\033[1;36m📚 Collections in the async store:\033[0m")
    for coll_name in collections:
        print(f"  - {coll_name}")

    print("\n\033[1;36m🎉 Quickstart complete! Explore more with AgentVectorDB.\033[0m")

if __name__ == "__main__":
    asyncio.run(async_example_main())
```

---

## 🛠️ API Overview

### `AgentVectorDBStore(db_path: str)`

- **db_path:** Directory where LanceDB database files are stored.

**Methods:**

- `get_or_create_collection(...)` – Create or open a collection.
- `list_collections()` – List all collections.
- `delete_collection(name: str)` – Delete a collection.

### `AgentMemoryCollection`

- **Properties:** `name`, `embedding_function`, `schema`
- **Methods:** `add`, `add_batch`, `query`, `get_by_id`, `delete`, `count`, `prune_memories`, `__len__`

### Asynchronous API

- `AsyncAgentVectorDBStore`
- `AsyncAgentMemoryCollection`
    - All methods of their synchronous counterparts are available as `async` methods.

---

## 📚 Advanced Usage

### Multiple Collections

```python
store = AgentVectorDBStore(db_path="./my_multi_agent_db")
kb_ef = DefaultTextEmbeddingFunction(dimension=128)
knowledge_base = store.get_or_create_collection(
    name="knowledge_base",
    embedding_function=kb_ef
)
knowledge_base.add(content="The Earth revolves around the Sun.", type="astronomy_fact")
```

### Filtering with `filter_sql`

```python
results = my_collection.query(
    query_text="relevant topic",
    k=5,
    filter_sql="type = 'log_entry' AND importance_score > 0.5 AND metadata.extra LIKE '%user123%'"
)
```

### Memory Pruning

```python
pruned_count = observations.prune_memories(
    max_age_seconds=86400 * 7,
    min_importance_score=0.3,
    filter_logic="AND",
    dry_run=False
)
print(f"Pruned {pruned_count} old/unimportant observations.")
```

---

## 🧑‍💻 More Examples

See the [`examples/`](./examples/) directory for:

- `quickstart.py` – Full sync & async demo
- `sync_basic_usage.py` – Minimal synchronous usage
- `async_batch_add.py` – Async batch add/query
- `metadata_filtering.py` – Metadata and SQL filtering
- `prune_and_count.py` – Pruning and counting
- `async_delete.py` – Async deletion

---

## 🛤️ Roadmap & Contributing

AgentVectorDB is actively evolving. Planned features include:
- More sophisticated filter builders
- Reflection/summarization helpers
- Schema evolution helpers
- Community-driven extensions

**Contributions are welcome!** Please see `CONTRIBUTING.md` for guidelines.

---

## 📄 License

This project is licensed under the Apache-2.0 License.

---

**AgentVectorDB: Give your AI agents a memory!**
