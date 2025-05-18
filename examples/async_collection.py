import asyncio
from typing import List, Dict, Any, Optional, Type

from .collection import AgentMemoryCollection
from .schemas import MemoryEntrySchema # For type hints (though schema property returns dynamic)
from pydantic import BaseModel # For schema property type hint

class AsyncAgentMemoryCollection:
    def __init__(self, sync_collection_instance: AgentMemoryCollection):
        if not isinstance(sync_collection_instance, AgentMemoryCollection):
            raise TypeError("sync_collection_instance must be an AgentMemoryCollection")
        self._sync_collection = sync_collection_instance

    @property
    def name(self) -> str: return self._sync_collection.name
    @property
    def embedding_function(self) -> Any: return self._sync_collection.embedding_function
    @property
    def schema(self) -> Type[BaseModel]: return self._sync_collection.schema # Returns DynamicSchema

    async def add(self, **kwargs: Any) -> str:
        return await asyncio.to_thread(self._sync_collection.add, **kwargs)

    async def add_batch(self, entries: List[Dict[str, Any]]) -> List[str]:
        return await asyncio.to_thread(self._sync_collection.add_batch, entries)

    async def query(self, query_vector: Optional[List[float]]=None, query_text: Optional[str]=None, k: int=5,
                    filter_sql: Optional[str]=None, select_columns: Optional[List[str]]=None,
                    include_vector: bool=False) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(
            self._sync_collection.query, query_vector=query_vector, query_text=query_text, k=k,
            filter_sql=filter_sql, select_columns=select_columns, include_vector=include_vector
        )

    async def get_by_id(self, entry_id: str, select_columns: Optional[List[str]]=None) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._sync_collection.get_by_id, entry_id, select_columns=select_columns)

    async def delete(self, entry_id: Optional[str]=None, filter_sql: Optional[str]=None) -> int:
        return await asyncio.to_thread(self._sync_collection.delete, entry_id=entry_id, filter_sql=filter_sql)

    async def count(self, filter_sql: Optional[str]=None) -> int:
        return await asyncio.to_thread(self._sync_collection.count, filter_sql=filter_sql)

    async def prune_memories(self, max_age_seconds: Optional[int]=None, min_importance_score: Optional[float]=None,
                             max_last_accessed_seconds: Optional[int]=None, filter_logic: str="AND",
                             custom_filter_sql_addon: Optional[str]=None, dry_run: bool=False) -> int:
        return await asyncio.to_thread(
            self._sync_collection.prune_memories, max_age_seconds=max_age_seconds,
            min_importance_score=min_importance_score, max_last_accessed_seconds=max_last_accessed_seconds,
            filter_logic=filter_logic, custom_filter_sql_addon=custom_filter_sql_addon, dry_run=dry_run
        )

    async def __len__(self) -> int: return await asyncio.to_thread(len, self._sync_collection)