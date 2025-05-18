import asyncio
import os
import shutil
from agentvectordb import AsyncAgentVectorDBStore
from agentvectordb.embeddings import DefaultTextEmbeddingFunction

print("\033[1;36m")
print("🧠❌ AgentVectorDB Async Delete Example ❌🧠")
print("Demonstrating async deletion of memories.\n")
print("\033[0m")

DB_DIR = "./_agentvectordb_async_delete_db"
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory):
        shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

cleanup_db_dir(DB_DIR)

async def main():
    store = AsyncAgentVectorDBStore(db_path=DB_DIR)
    collection = await store.get_or_create_collection(
        name="delete_memories",
        embedding_function=ef,
        recreate=True
    )
    await collection.add(content="Delete me! 🗑️", type="temp")
    await collection.add(content="Keep me! 💾", type="perm")
    print(f"\033[1;34m📝 Count before delete: \033[1;33m{await collection.count()}\033[0m")
    deleted = await collection.delete(filter_sql="type = 'temp'")
    print(f"\033[1;31m🗑️ Deleted {deleted} entries.\033[0m")
    print(f"\033[1;34m📝 Count after delete: \033[1;33m{await collection.count()}\033[0m")
    print("\n\033[1;36m🎉 Async delete demo complete!\033[0m")

if __name__ == "__main__":
    asyncio.run(main())