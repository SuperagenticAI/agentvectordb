import time
import os
import shutil
import sys

# Ensure agentvector is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentvector import AgentMemory
from agentvector.embeddings import DefaultTextEmbeddingFunction

# --- Configuration ---
DB_DIR_COGNITIVE = "./_agentvector_cognitive_db"
TABLE_NAME = "cognitive_tests_main"
ef = DefaultTextEmbeddingFunction(dimension=64) # Smaller dimension for this example
VECTOR_DIMENSION = ef.ndims()

def cleanup_cognitive_db():
    if os.path.exists(DB_DIR_COGNITIVE):
        shutil.rmtree(DB_DIR_COGNITIVE)
    os.makedirs(DB_DIR_COGNITIVE, exist_ok=True)

# Example summarization callback for reflect_and_summarize
def simple_summarizer_callback(memories_retrieved: list[dict], topic: str) -> tuple[str, list[float]]:
    """
    A simple summarizer. In a real agent, this would likely involve an LLM.
    """
    print(f"\n--- Summarization Callback Invoked ---")
    print(f"Topic: '{topic}'")
    print(f"Number of memories to summarize: {len(memories_retrieved)}")
    
    if not memories_retrieved:
        summary_text = f"No specific information found to summarize for topic: {topic}."
        summary_vector = ef.generate([summary_text])[0]
        return summary_text, summary_vector

    # Concatenate content of memories for a simple summary
    content_to_summarize = [mem.get('content', '') for mem in memories_retrieved]
    combined_content = ". ".join(filter(None, content_to_summarize))
    
    summary_text = f"Summary for '{topic}': Based on {len(memories_retrieved)} memories, key points include: " \
                   f"{combined_content[:150]}..." # Truncate for brevity
    
    # Generate embedding for the summary
    summary_vector = ef.generate([summary_text])[0]
    
    print(f"Generated Summary: \"{summary_text}\"")
    print(f"--- End Summarization Callback ---\n")
    return summary_text, summary_vector


def run_cognitive_examples():
    cleanup_cognitive_db()
    print(f"Using AgentVector DB for cognitive functions at: {DB_DIR_COGNITIVE}")

    memory = AgentMemory(
        db_path=DB_DIR_COGNITIVE,
        table_name=TABLE_NAME,
        embedding_function=ef,
        recreate_table=True, # Start fresh
        update_last_accessed_on_query=True # Important for pruning by last_accessed
    )

    print("--- Populating with diverse memories for cognitive function tests ---")
    current_ts = time.time()
    mem_ids = memory.add_batch([
        {"content": "Project Alpha initial specification document.", "type": "document_chunk", "timestamp_created": current_ts - 86400*45, "timestamp_last_accessed": current_ts - 86400*40, "importance_score": 0.9, "tags": ["project_alpha", "spec"]},
        {"content": "User feedback: 'Project Alpha UI is confusing.'", "type": "user_feedback", "timestamp_created": current_ts - 86400*35, "timestamp_last_accessed": current_ts - 86400*30, "importance_score": 0.7, "tags": ["project_alpha", "ui_ux"]},
        {"content": "Daily log: System status normal.", "type": "log_entry", "timestamp_created": current_ts - 86400*10, "timestamp_last_accessed": current_ts - 86400*9, "importance_score": 0.2, "tags": ["system_status"]},
        {"content": "Meeting notes: Discussed Project Beta strategy.", "type": "meeting_note", "timestamp_created": current_ts - 86400*5, "timestamp_last_accessed": current_ts - 86400*1, "importance_score": 0.8, "tags": ["project_beta", "strategy"]},
        {"content": "Random thought: What if AI could dream?", "type": "fleeting_thought", "timestamp_created": current_ts - 86400*2, "timestamp_last_accessed": None, "importance_score": 0.3, "tags": ["ai_philosophy"]}, # Never accessed
        {"content": "Critical alert: Database connection lost for service Gamma.", "type": "alert", "timestamp_created": current_ts - 3600*1, "timestamp_last_accessed": current_ts - 300, "importance_score": 1.0, "tags": ["service_gamma", "critical_issue"]},
    ])
    print(f"Populated {len(mem_ids)} initial memories. Total count: {len(memory)}")

    # --- Test Memory Pruning ---
    print("\n--- Testing Memory Pruning ---")
    # Scenario 1: Prune very old (older than 40 days) AND low importance (score < 0.75)
    # Expected: "User feedback: 'Project Alpha UI is confusing.'" (45 days old, score 0.7) might be pruned.
    #           "Project Alpha initial specification document." (45 days old, score 0.9) should NOT be pruned by this.
    print("\nPruning Scenario 1: Very old AND low importance memories...")
    pruned_s1 = memory.prune_memories(
        max_age_seconds=86400 * 40, # Older than 40 days
        min_importance_score=0.75,  # Importance strictly LESS than 0.75
        filter_logic="AND",
        dry_run=False
    )
    print(f"Scenario 1: Pruned {pruned_s1} memories. Count now: {len(memory)}")

    # Scenario 2: Prune items not accessed in 8 days OR with very low importance (score < 0.25)
    # Expected: "Daily log: System status normal." (accessed 9 days ago, score 0.2) should be pruned.
    print("\nPruning Scenario 2: Stale OR very low importance memories...")
    pruned_s2 = memory.prune_memories(
        max_last_accessed_seconds=86400 * 8, # Not accessed in last 8 days
        min_importance_score=0.25, # Importance < 0.25
        filter_logic="OR", # Prune if EITHER condition met
        dry_run=False
    )
    print(f"Scenario 2: Pruned {pruned_s2} memories. Count now: {len(memory)}")

    # --- Test Reflection and Summarization ---
    print("\n--- Testing Reflection and Summarization for 'Project Alpha' ---")
    # Simulate some activity on Project Alpha memories to update their last_accessed
    alpha_query_results = memory.query(query_text="Project Alpha", k=2, filters={"tags": {"$contains": "project_alpha"}})
    print(f"Queried for Project Alpha, found {len(alpha_query_results)} relevant items (updates last_accessed).")

    # Perform reflection
    summary_id = memory.reflect_and_summarize(
        query_text="Project Alpha Learnings", # Topic for the summarizer
        summarization_callback=simple_summarizer_callback, # Our example callback
        k_to_retrieve=3, # Retrieve top 3 memories about Project Alpha for summarization
        query_filters={"tags": {"$contains": "project_alpha"}},
        new_memory_type="project_summary",
        new_memory_source="cognitive_reflection_module",
        new_memory_tags=["project_alpha", "reflection_output", "v1_summary"],
        new_memory_importance=0.98,
        delete_original_memories=False # Set to True to test replacing originals
    )

    if summary_id:
        print(f"Reflection successful. New summary memory created with ID: {summary_id}")
        summary_entry = memory.get_by_id(summary_id)
        if summary_entry:
            print(f"  Summary Content: '{summary_entry.get('content')}'")
            print(f"  Summary relates to original memories: {summary_entry.get('related_memories')}")
            print(f"  Summary importance: {summary_entry.get('importance_score')}")
    else:
        print("Reflection process did not create a summary memory.")

    print(f"\nFinal memory count after all cognitive operations: {len(memory)}")

    # List remaining memories for inspection
    print("\n--- Final State of Memories ---")
    all_memories = memory.query(query_text="anything", k=len(memory), include_vector=False) # Crude way to get all
    if all_memories:
        for i, mem in enumerate(all_memories):
            print(f"  {i+1}. ID: {mem.get('id')[:8]}... Content: '{mem.get('content', '')[:50]}...' "
                  f"Type: {mem.get('type')} Score: {mem.get('importance_score')} "
                  f"Created: {time.strftime('%Y-%m-%d', time.localtime(mem.get('timestamp_created',0)))} "
                  f"Accessed: {time.strftime('%Y-%m-%d', time.localtime(mem.get('timestamp_last_accessed',0))) if mem.get('timestamp_last_accessed') else 'Never'}")
    else:
        print("No memories remaining.")


if __name__ == "__main__":
    run_cognitive_examples()
    print("\nCognitive Functions example finished.")
    # Inspect DB_DIR_COGNITIVE for persisted data.