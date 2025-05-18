import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple

from .agent_memory import AgentMemory  # The synchronous class


class AsyncAgentMemory:
    """
    Asynchronous wrapper for AgentMemory, using asyncio.to_thread for non-blocking operations.
    This makes AgentVectorDB compatible with async-first agent frameworks.
    """

    def __init__(self, sync_memory_instance: AgentMemory):
        """
        Initializes AsyncAgentMemory.

        Args:
            sync_memory_instance: A fully configured instance of the synchronous AgentMemory.
        """
        if not isinstance(sync_memory_instance, AgentMemory):
            raise TypeError("sync_memory_instance must be an instance of agentvectordb.AgentMemory")
        self._sync_memory = sync_memory_instance

    @property
    def db_path(self) -> str:
        """Path to the LanceDB database directory."""
        return self._sync_memory.db_path

    @property
    def table_name(self) -> str:
        """Name of the table used for memories."""
        return self._sync_memory.table_name

    @property
    def table(self):  # Access to underlying LanceTable, if needed (use with caution in async)
        """Direct access to the underlying LanceDB Table object. Use with caution in async contexts."""
        return self._sync_memory.table

    async def add(self, **kwargs: Any) -> str:
        """Asynchronously adds a single memory entry."""
        return await asyncio.to_thread(self._sync_memory.add, **kwargs)

    async def add_batch(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Asynchronously adds a batch of memory entries."""
        return await asyncio.to_thread(self._sync_memory.add_batch, entries)

    async def query(self, **kwargs: Any) -> List[Dict[str, Any]]:
        """Asynchronously queries the memory database."""
        return await asyncio.to_thread(self._sync_memory.query, **kwargs)

    async def get_by_id(self, entry_id: str, select_columns: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Asynchronously retrieves a memory entry by its ID."""
        return await asyncio.to_thread(self._sync_memory.get_by_id, entry_id, select_columns=select_columns)

    async def delete(self, entry_id: Optional[str] = None, filter_sql: Optional[str] = None) -> int:
        """
        Asynchronously deletes memory entries.
        Returns the number of entries matched by the filter before deletion attempt.
        """
        return await asyncio.to_thread(self._sync_memory.delete, entry_id=entry_id, filter_sql=filter_sql)

    async def count(self, filters: Optional[Dict[str, Any]] = None, filter_sql: Optional[str] = None) -> int:
        """Asynchronously counts entries, optionally filtered."""
        return await asyncio.to_thread(self._sync_memory.count, filters=filters, filter_sql=filter_sql)

    async def prune_memories(self, **kwargs: Any) -> int:
        """Asynchronously prunes memories based on specified criteria."""
        return await asyncio.to_thread(self._sync_memory.prune_memories, **kwargs)

    async def reflect_and_summarize(
        self,
        summarization_callback: Callable[[List[Dict], str], Tuple[str, List[float]]],
        **kwargs: Any,  # All other args for reflect_and_summarize
    ) -> Optional[str]:
        """
        Asynchronously facilitates agent reflection and summarization.
        The summarization_callback itself is called within the thread, so it should be thread-safe
        if it performs I/O or accesses shared state. If the callback is async,
        it needs to be handled appropriately (e.g. by running its own event loop snippet if called from a thread,
        or redesigning reflect_and_summarize to be natively async).
        """
        # Pass the callback directly. If it's an async function, the user needs to be aware
        # that it will be run in a separate thread by asyncio.to_thread, and how that interacts
        # with event loops if the callback itself tries to manage one.
        # For most CPU-bound or simple I/O callbacks, this should be fine.
        return await asyncio.to_thread(
            self._sync_memory.reflect_and_summarize,
            summarization_callback=summarization_callback,  # Pass callback explicitly
            **kwargs,
        )

    async def list_tables(self) -> List[str]:
        """Asynchronously lists all tables in the database connection."""
        return await asyncio.to_thread(self._sync_memory.list_tables)

    async def __len__(self) -> int:
        """Asynchronously returns the total number of entries in the current table."""
        return await asyncio.to_thread(len, self._sync_memory)

    async def close(self):
        """Asynchronously 'closes' the AgentMemory (currently a no-op for LanceDB connection)."""
        await asyncio.to_thread(self._sync_memory.close)
