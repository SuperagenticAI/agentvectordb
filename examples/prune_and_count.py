import os
import shutil
from agentvectordb import AgentVectorDBStore
from agentvectordb.embeddings import DefaultTextEmbeddingFunction

print("\033[1;36m")
print("🧠🧹 AgentVectorDB Prune & Count Example 🧹🧠")
print("Demonstrating memory pruning and counting.\n")
print("\033[0m")

DB_DIR = "./_agentvectordb_prune_db"
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory):
        shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

cleanup_db_dir(DB_DIR)

store = AgentVectorDBStore(db_path=DB_DIR)
memories = store.get_or_create_collection(
    name="prune_memories",
    embedding_function=ef,
    recreate=True
)

for i in range(5):
    memories.add(
        content=f"Memory {i}",
        type="test",
        importance_score=0.1 * i
    )

print(f"\033[1;34m📝 Total before prune: \033[1;33m{len(memories)}\033[0m")
pruned = memories.prune_memories(min_importance_score=0.3)
print(f"\033[1;31m🗑️ Pruned {pruned} memories.\033[0m")
print(f"\033[1;34m📝 Total after prune: \033[1;33m{len(memories)}\033[0m")
print("\n\033[1;36m🎉 Pruning demo complete!\033[0m")
