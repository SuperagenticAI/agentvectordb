# filepath: examples/quickstart.py
import asyncio
import os
import shutil
from agentvector import AgentVectorStore, AsyncAgentVectorStore
from agentvector.embeddings import DefaultTextEmbeddingFunction

# --- AgentVector Banner ---
print("\033[1;36m")
print("🧠🚀 Welcome to AgentVector Quickstart! 🚀🧠")
print("A lightweight, embeddable vector database for agentic AI systems, built on LanceDB.\n")
print("\033[0m")

DB_DIR = "./_agentvector_mvp_quickstart_db"
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory):
        shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

cleanup_db_dir(DB_DIR)

# --- Synchronous API ---
print("\033[1;34m🔹 [SYNC] Episodic Memory Demo\033[0m")
store = AgentVectorStore(db_path=DB_DIR)
episodic_memories = store.get_or_create_collection(
    name="episodic_stream",
    embedding_function=ef,
    update_last_accessed_on_query=True,
    recreate=True
)
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
query_results = episodic_memories.query(
    query_text="AgentVector collection feature",
    k=1,
    filter_sql="type = 'user_interaction'"
)
print("\033[1;32m\n🌟 Sync Query Results:\033[0m")
for res in query_results:
    print(f"\033[1;33m  • {res.get('content', 'N/A')} \033[0m\033[0;35m(Type: {res.get('type')})\033[0m")

# --- Asynchronous API ---
async def async_example_main():
    print("\n\033[1;34m🔹 [ASYNC] Agent Thoughts Log Demo\033[0m")
    async_store = AsyncAgentVectorStore(db_path=DB_DIR)
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

    print("\n\033[1;36m🎉 Quickstart complete! Explore more with AgentVector.\033[0m")

if __name__ == "__main__":
    asyncio.run(async_example_main())