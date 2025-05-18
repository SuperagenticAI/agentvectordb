import asyncio
from typing import List, Optional, Type, Any

from .store import AgentVectorStore
from .collection import AgentMemoryCollection 
from .async_collection import AsyncAgentMemoryCollection
from .schemas import MemoryEntrySchema

class AsyncAgentVectorStore:
    def __init__(self, db_path: str):
        self._sync_store = AgentVectorStore(db_path=db_path)

    @property
    def db_path(self) -> str: return self._sync_store.db_path

    async def get_or_create_collection(
        self, name: str, embedding_function: Optional[Any] = None,
        base_schema: Type[MemoryEntrySchema] = MemoryEntrySchema,
        vector_dimension: Optional[int] = None,
        update_last_accessed_on_query: bool = False, recreate: bool = False
    ) -> AsyncAgentMemoryCollection:
        sync_collection = await asyncio.to_thread(
            self._sync_store.get_or_create_collection, name=name,
            embedding_function=embedding_function, base_schema=base_schema,
            vector_dimension=vector_dimension,
            update_last_accessed_on_query=update_last_accessed_on_query, recreate=recreate
        )
        return AsyncAgentMemoryCollection(sync_collection)

    async def get_collection(self, name: str) -> Optional[AsyncAgentMemoryCollection]:
        sync_collection = await asyncio.to_thread(self._sync_store.get_collection, name)
        return AsyncAgentMemoryCollection(sync_collection) if sync_collection else None

    async def list_collections(self) -> List[str]:
        return await asyncio.to_thread(self._sync_store.list_collections)

    async def delete_collection(self, name: str) -> bool:
        return await asyncio.to_thread(self._sync_store.delete_collection, name)

    async def close(self): await asyncio.to_thread(self._sync_store.close)
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): await self.close()