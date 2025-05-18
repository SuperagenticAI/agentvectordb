import os
import shutil
from agentvectordb import AgentVectorDBStore
from agentvectordb.embeddings import DefaultTextEmbeddingFunction

# --- AgentVectorDB Demo Banner ---
print("\033[1;36m")
print("🧠✨ Welcome to AgentVectorDB! ✨🧠")
print("A lightweight, embeddable vector database for agentic AI systems, built on LanceDB.\n")
print("\033[0m")

DB_DIR = "./_agentvectordb_sync_example_db"
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory):
        shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

cleanup_db_dir(DB_DIR)

print("\033[1;34m🔹 [SYNC] Creating and querying a simple memory collection...\033[0m")

store = AgentVectorDBStore(db_path=DB_DIR)
memories = store.get_or_create_collection(
    name="simple_memories",
    embedding_function=ef,
    recreate=True
)

memories.add(
    content="The Eiffel Tower is in Paris.",
    type="fact",
    importance_score=0.9
)
memories.add(
    content="AgentVectorDB supports LanceDB.",
    type="feature",
    importance_score=0.8
)

results = memories.query(query_text="Paris", k=2)
print("\033[1;32m\n🌟 Query Results:\033[0m")
for res in results:
    print(f"\033[1;33m  • {res['content']} \033[0m\033[0;35m(type: {res['type']})\033[0m")

print("\n\033[1;36m🎉 Done! Explore more with AgentVectorDB.\033[0m")
