import asyncio
import os
import shutil
from agentvectordb import AsyncAgentVectorDBStore
from agentvectordb.embeddings import DefaultTextEmbeddingFunction

print("\033[1;36m")
print("🧠🚀 AgentVectorDB Async Batch Example 🚀🧠")
print("Store and search memories asynchronously with style!\n")
print("\033[0m")

DB_DIR = "./_agentvectordb_async_batch_db"
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory):
        shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

cleanup_db_dir(DB_DIR)

async def main():
    print("\033[1;34m🔹 [ASYNC] Adding a batch of memories...\033[0m")
    store = AsyncAgentVectorDBStore(db_path=DB_DIR)
    collection = await store.get_or_create_collection(
        name="batch_memories",
        embedding_function=ef,
        recreate=True
    )
    await collection.add_batch([
        {"content": "🍏 Apple is a fruit.", "type": "fact"},
        {"content": "🗼 Paris is in France.", "type": "fact"},
        {"content": "🤖 AgentVectorDB is cool.", "type": "opinion"}
    ])
    results = await collection.query(query_text="France", k=2)
    print("\033[1;32m\n🌟 Async Batch Query Results:\033[0m")
    for res in results:
        print(f"\033[1;33m  • {res['content']} \033[0m\033[0;35m(type: {res['type']})\033[0m")
    print("\n\033[1;36m🎉 Async batch demo complete!\033[0m")

if __name__ == "__main__":
    asyncio.run(main())
