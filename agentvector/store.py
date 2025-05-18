import os
import lancedb
from typing import List, Optional, Type, Any, Dict

from .collection import AgentMemoryCollection
from .schemas import MemoryEntrySchema
from .exceptions import InitializationError, OperationError

class AgentVectorStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        try:
            os.makedirs(self.db_path, exist_ok=True)
            self.db = lancedb.connect(self.db_path)
            # print(f"AgentVectorStore initialized at path: {self.db_path}") # Less verbose for tests
        except Exception as e:
            raise InitializationError(f"Failed to connect/init LanceDB at {self.db_path}: {e}")
        self._collections_cache: Dict[str, AgentMemoryCollection] = {}

    def get_or_create_collection(
        self, name: str, embedding_function: Optional[Any] = None,
        base_schema: Type[MemoryEntrySchema] = MemoryEntrySchema,
        vector_dimension: Optional[int] = None,
        update_last_accessed_on_query: bool = False,
        recreate: bool = False
    ) -> AgentMemoryCollection:
        # If recreate is True, we must not return from cache, and collection init will handle drop.
        if name in self._collections_cache and not recreate:
            # TODO: Add logic to check if parameters differ from cached collection's config.
            # For MVP, if not recreating, return cached. This assumes parameters match.
            # A mismatch in parameters for an existing cached collection should ideally error or warn.
            # For now, this simple caching is fine for MVP.
            return self._collections_cache[name]

        collection_instance = AgentMemoryCollection(
            db_connection=self.db, name=name, base_schema=base_schema,
            vector_dimension=vector_dimension, embedding_function=embedding_function,
            update_last_accessed_on_query=update_last_accessed_on_query, recreate=recreate
        )
        self._collections_cache[name] = collection_instance
        return collection_instance

    def get_collection(self, name: str) -> Optional[AgentMemoryCollection]:
        # MVP: get_collection primarily returns cached collections.
        # Robustly opening an arbitrary existing table from disk and rehydrating its exact
        # AgentMemoryCollection Python object configuration (EF instance, base_schema type, etc.)
        # is complex as this metadata isn't stored by LanceDB in a way AgentVector can easily retrieve.
        # Users should use get_or_create_collection to ensure consistent configuration.
        if name in self._collections_cache:
            return self._collections_cache[name]
        
        # If it's in DB but not cache, what EF/schema was it created with? We don't know.
        # So, for MVP, we won't try to auto-rehydrate with guessed params.
        if name in self.db.table_names():
            print(f"Warning: Collection '{name}' exists in DB but was not created in this Store session. "
                  f"Use get_or_create_collection with original parameters to access it.")
        return None

    def list_collections(self) -> List[str]:
        try: return self.db.table_names()
        except Exception as e: raise OperationError(f"Failed to list collections: {e}")

    def delete_collection(self, name: str) -> bool:
        if name in self._collections_cache: del self._collections_cache[name]
        if name not in self.db.table_names(): return True # Idempotent
        try:
            self.db.drop_table(name)
            # print(f"Successfully deleted collection: {name}") # Less verbose for tests
            return True
        except Exception as e: raise OperationError(f"Failed to delete collection '{name}': {e}")

    def close(self): pass # LanceDB connection usually doesn't need explicit close

    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): self.close()