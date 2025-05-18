import os
import shutil
from agentvectordb import AgentVectorDBStore
from agentvectordb.embeddings import DefaultTextEmbeddingFunction

print("\033[1;36m")
print("🧠🔍 AgentVectorDB Metadata Filtering Example 🔍🧠")
print("Showcasing metadata and SQL-like filtering.\n")
print("\033[0m")

DB_DIR = "./_agentvectordb_metadata_db"
ef = DefaultTextEmbeddingFunction(dimension=64)

def cleanup_db_dir(db_directory):
    if os.path.exists(db_directory):
        shutil.rmtree(db_directory)
    os.makedirs(db_directory, exist_ok=True)

cleanup_db_dir(DB_DIR)

store = AgentVectorDBStore(db_path=DB_DIR)
memories = store.get_or_create_collection(
    name="metadata_memories",
    embedding_function=ef,
    recreate=True
)

memories.add(
    content="This is a memory about Project X.",
    type="project_note",
    metadata={"project": "X", "owner": "alice"}
)
memories.add(
    content="This is a memory about Project Y.",
    type="project_note",
    metadata={"project": "Y", "owner": "bob"}
)

results = memories.query(
    query_text="project",
    k=2,
    filter_sql="metadata.extra LIKE '%alice%'"
)
print("\033[1;32m\n🌟 Metadata Filter Query Results:\033[0m")
for res in results:
    print(f"\033[1;33m  • {res['content']} \033[0m\033[0;35m(metadata: {res['metadata']})\033[0m")

print("\n\033[1;36m🎉 Metadata filtering demo complete!\033[0m")
