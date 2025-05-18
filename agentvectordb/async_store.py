import os
import lancedb
import asyncio
from typing import List, Optional, Type, Any, Dict

from .store import AgentVectorDBStore
from .collection import AgentMemoryCollection
from .schemas import MemoryEntrySchema
from .exceptions import InitializationError, OperationError
from .async_collection import AsyncAgentMemoryCollection

class AsyncAgentVectorDBStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Use the sync store for all actual DB operations
        self._sync_store = AgentVectorDBStore(db_path=db_path)
        self._collections_cache: Dict[str, AgentMemoryCollection] = {}

    async def get_or_create_collection(
        self, name: str, embedding_function: Optional[Any] = None,
        base_schema: Type[MemoryEntrySchema] = MemoryEntrySchema,
        vector_dimension: Optional[int] = None,
        update_last_accessed_on_query: bool = False,
        recreate: bool = False
    ) -> "AsyncAgentMemoryCollection":
        # Always use the sync store's get_or_create_collection, which creates if needed
        sync_collection = await asyncio.to_thread(
            self._sync_store.get_or_create_collection,
            name=name,
            embedding_function=embedding_function,
            base_schema=base_schema,
            vector_dimension=vector_dimension,
            update_last_accessed_on_query=update_last_accessed_on_query,
            recreate=recreate
        )
        from .async_collection import AsyncAgentMemoryCollection
        return AsyncAgentMemoryCollection(sync_collection)

    def get_collection(self, name: str) -> Optional[AgentMemoryCollection]:
        # MVP: get_collection primarily returns cached collections.
        # Robustly opening an arbitrary existing table from disk and rehydrating its exact
        # AgentMemoryCollection Python object configuration (EF instance, base_schema type, etc.)
        # is complex as this metadata isn't stored by LanceDB in a way AgentVectorDB can easily retrieve.
        # Users should use get_or_create_collection to ensure consistent configuration.
        if name in self._collections_cache:
            return self._collections_cache[name]
        
        # If it's in DB but not cache, what EF/schema was it created with? We don't know.
        # So, for MVP, we won't try to auto-rehydrate with guessed params.
        if name in self.db.table_names():
            print(f"Warning: Collection '{name}' exists in DB but was not created in this Store session. "
                  f"Use get_or_create_collection with original parameters to access it.")
        return None

    async def list_collections(self) -> list[str]:
        return await asyncio.to_thread(self._sync_store.list_collections)

    async def delete_collection(self, name: str) -> bool:
        return await asyncio.to_thread(self._sync_store.delete_collection, name)

    async def close(self):
        await asyncio.to_thread(self._sync_store.close)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def create_indexes(self, table):
        # After you create the table (table = self.db.create_table(...))
        if table.count_rows() >= 2:
            try:
                table.create_index(
                    vector_column_name="vector",
                    index_type="IVF_FLAT",
                    num_partitions=2
                )
            except Exception as e:
                print(f"Warning: Could not create vector index: {e}")
        else:
            print("Skipping vector index creation: not enough rows for KMeans.")

        try:
            table.create_fts_index("content")
        except Exception as e:
            print(f"Warning: Could not create text index: {e}")