import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

import lancedb
from lancedb.table import Table
from pydantic import ValidationError

from .exceptions import EmbeddingError, InitializationError, OperationError, QueryError, SchemaError
from .schemas import MemoryEntrySchema, create_dynamic_memory_entry_schema
from .utils import build_filter_sql


class AgentMemory:
    """
    Manages an agent's memory using LanceDB as a vector store.
    Designed for agent-centric operations like semantic search, filtering,
    memory decay, and reflection.
    """

    def __init__(
        self,
        db_path: str,
        table_name: str = "memories",
        base_schema: Type[MemoryEntrySchema] = MemoryEntrySchema,
        vector_dimension: Optional[int] = None,
        embedding_function: Optional[
            Any
        ] = None,  # LanceDB EmbeddingFunctionLike or AgentVectorDB's BaseEmbeddingFunction
        recreate_table: bool = False,
        update_last_accessed_on_query: bool = False,
    ):
        """
        Initializes AgentMemory.

        Args:
            db_path (str): Path to the LanceDB database directory.
            table_name (str): Name of the table to use/create for memories.
            base_schema (Type[MemoryEntrySchema]): Pydantic base schema for memory entries.
            vector_dimension (Optional[int]): Dimension of the vectors.
                Required if not using an embedding_function that defines `ndims()`,
                or if adding raw vectors without an embedding_function.
            embedding_function (Optional[Any]): A LanceDB compatible embedding function.
                If provided, AgentVectorDB can automatically embed content.
                This function should ideally have `source_column()` and `ndims()` methods.
            recreate_table (bool): If True, drops the table if it exists and creates a new one.
            update_last_accessed_on_query (bool): If True, automatically updates `timestamp_last_accessed`
                                                  for entries retrieved via `query` or `get_by_id`.
        """
        self.db_path = db_path
        self.table_name = table_name
        self.embedding_function = embedding_function
        self.update_last_accessed_on_query = update_last_accessed_on_query

        self._vector_dimension = vector_dimension
        if self.embedding_function and hasattr(self.embedding_function, "ndims"):
            ef_dim = self.embedding_function.ndims()
            if self._vector_dimension and self._vector_dimension != ef_dim:
                raise InitializationError(
                    f"Provided vector_dimension ({self._vector_dimension}) conflicts with "
                    f"embedding_function's dimension ({ef_dim})."
                )
            self._vector_dimension = ef_dim  # Prefer EF's dimension

        if not self._vector_dimension:
            # If no EF and no explicit dimension, this is an issue if adding raw vectors
            # or if EF doesn't define ndims. We raise error early if no way to know dim.
            raise InitializationError(
                "vector_dimension must be provided if not using an embedding_function "
                "that defines its output dimension (ndims), or if adding raw vectors."
            )

        try:
            self.db = lancedb.connect(self.db_path)
        except Exception as e:
            raise InitializationError(f"Failed to connect to LanceDB at {self.db_path}: {e}")

        if not issubclass(base_schema, MemoryEntrySchema):
            raise SchemaError("base_schema must be a subclass of agentvectordb.schemas.MemoryEntrySchema.")
        self.BaseSchema = base_schema

        # Determine the final Pydantic schema for LanceDB table creation
        # If using an embedding function that integrates with LanceModel, LanceDB might handle schema creation.
        # For explicit schema control, we use create_dynamic_memory_entry_schema.
        self.DynamicSchema = create_dynamic_memory_entry_schema(self.BaseSchema, self._vector_dimension)

        if recreate_table and self.table_name in self.db.table_names():
            try:
                self.db.drop_table(self.table_name)
                print(f"Dropped existing table: {self.table_name}")
            except Exception as e:
                raise OperationError(f"Failed to drop table {self.table_name}: {e}")

        self.table: Optional[Table] = None  # Initialize to None
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Ensures the LanceDB table exists with the correct schema."""
        try:
            if self.table_name not in self.db.table_names():
                print(
                    f"Table '{self.table_name}' not found. Creating new table with schema {self.DynamicSchema.__name__}."
                )
                # LanceDB 0.6.0+ `create_table` can take `schema` (Pydantic model) and `embedding_functions` (list of EF)
                # The `embedding_functions` arg is for LanceDB to manage embedding generation from source columns.
                ef_config = None
                if self.embedding_function:
                    # LanceDB expects a list of EmbeddingFunctionConfig for the `embedding_functions` argument
                    # This config maps source columns to vector columns using specific EFs.
                    # Simplification: if our EF has source_column, make a config.
                    if hasattr(self.embedding_function, "source_column") and hasattr(
                        self.embedding_function, "generate"
                    ):
                        from lancedb.embeddings import EmbeddingFunctionConfig

                        ef_config = [
                            EmbeddingFunctionConfig(
                                source_column=self.embedding_function.source_column(),
                                vector_column="vector",  # Assuming 'vector' is our target vector field
                                function=self.embedding_function,
                            )
                        ]
                    else:
                        print(
                            "Warning: Provided embedding_function doesn't conform to expected LanceDB EF structure for auto-config. Manual vector provision or ensure EF is LanceDB native."
                        )

                self.table = self.db.create_table(
                    self.table_name,
                    schema=self.DynamicSchema,
                    embedding_functions=ef_config,  # Pass the config list
                    mode="create",  # Explicitly create
                )
                print(f"Table '{self.table_name}' created successfully.")
            else:
                self.table = self.db.open_table(self.table_name)
                print(f"Opened existing table: {self.table_name}")
                # TODO: Optionally, verify schema of existing table.
                # LanceDB table.schema provides Arrow schema. Comparing can be complex.
        except Exception as e:
            raise InitializationError(f"Failed to create or open table '{self.table_name}': {e}")

    def _prepare_data_for_add(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Prepares a single data dictionary for adding to LanceDB."""
        # Ensure ID and timestamps
        if "id" not in data_dict or not data_dict["id"]:
            data_dict["id"] = str(uuid.uuid4())
        if "timestamp_created" not in data_dict:
            data_dict["timestamp_created"] = time.time()

        # If vector is provided, validate its dimension
        if "vector" in data_dict and data_dict["vector"] is not None:
            if len(data_dict["vector"]) != self._vector_dimension:
                raise SchemaError(
                    f"Provided vector for ID '{data_dict['id']}' has dimension {len(data_dict['vector'])}, "
                    f"but table expects {self._vector_dimension}."
                )
        # If no vector and no EF capable of generating from 'content' (or other source_column)
        elif "vector" not in data_dict and not self.embedding_function:
            raise EmbeddingError(
                f"Entry ID '{data_dict['id']}' has no 'vector' and no embedding_function is configured."
            )
        elif "vector" not in data_dict and self.embedding_function:
            if not hasattr(self.embedding_function, "source_column") or not data_dict.get(
                self.embedding_function.source_column()
            ):
                raise EmbeddingError(
                    f"Entry ID '{data_dict['id']}' has no 'vector'. Embedding function is configured "
                    f"but its source column ('{getattr(self.embedding_function, 'source_column', 'N/A')()}' value not found in data."
                )
            # If EF is configured and source column data exists, LanceDB will handle embedding on add.

        # Validate with Pydantic schema (excluding vector if EF will generate it)
        try:
            # Schema for validation shouldn't strictly require 'vector' if EF handles it.
            # However, our DynamicSchema *does* include 'vector'.
            # For now, assume data passed to add for EF case has 'content' (or source_col) and other fields.
            # LanceDB's .add() will do the Pydantic conversion if schema is Pydantic model.
            # For robustness, we can validate non-vector parts here.
            # Minimal validation here, rely on LanceDB's Pydantic integration.
            self.DynamicSchema.model_validate(data_dict, context={"skip_vector_if_ef": bool(self.embedding_function)})
        except ValidationError as e:
            raise SchemaError(f"Data validation failed for entry ID '{data_dict['id']}': {e}")

        return data_dict

    def add(
        self,
        **kwargs: Any,  # Memory entry fields as keyword arguments
    ) -> str:
        """
        Adds a single memory entry to the database.
        If an `embedding_function` is configured and its `source_column` (e.g., 'content')
        is provided but 'vector' is not, the content will be embedded automatically by LanceDB.

        Args:
            **kwargs: Fields for the memory entry, matching the schema (e.g., content, vector, type).
                      'id' and 'timestamp_created' are auto-generated if not provided.

        Returns:
            str: The ID of the added memory entry.
        """
        if not self.table:
            raise InitializationError("Table not initialized.")

        entry_data = self._prepare_data_for_add(kwargs.copy())  # Use copy

        try:
            self.table.add([entry_data])  # LanceDB expects a list of dicts
            return entry_data["id"]
        except Exception as e:
            raise OperationError(f"Failed to add memory entry (ID: {entry_data.get('id')}): {e}")

    def add_batch(self, entries: List[Dict[str, Any]]) -> List[str]:
        """
        Adds a batch of memory entries to the database.

        Args:
            entries: A list of dictionaries, each representing a memory entry.

        Returns:
            List[str]: A list of IDs of the added memory entries.
        """
        if not self.table:
            raise InitializationError("Table not initialized.")
        if not entries:
            return []

        processed_entries = [self._prepare_data_for_add(entry.copy()) for entry in entries]
        entry_ids = [entry["id"] for entry in processed_entries]

        try:
            self.table.add(processed_entries)
            return entry_ids
        except Exception as e:
            # Attempt to find which entry might have caused the error if possible (hard with batch)
            raise OperationError(f"Failed to add batch memory entries: {e}")

    def _update_last_accessed(self, entry_ids: List[str]):
        """Internal helper to update timestamp_last_accessed for given entry IDs."""
        if not entry_ids or not self.table:
            return
        try:
            # LanceDB table.update(where=..., values=...)
            # This assumes LanceDB version supports robust update.
            ids_sql_list = ", ".join([f"'{str(eid)}'" for eid in entry_ids])
            filter_condition = f"id IN ({ids_sql_list})"
            self.table.update(values={"timestamp_last_accessed": time.time()}, where=filter_condition)
        except Exception as e:
            # Log error, but don't let it break the main operation (e.g., query)
            print(f"Warning: Failed to update timestamp_last_accessed for IDs {entry_ids}: {e}")

    def query(
        self,
        query_vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        filter_sql: Optional[str] = None,
        select_columns: Optional[List[str]] = None,
        include_vector: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Queries the memory database for entries similar to the query_vector or query_text.

        Args:
            query_vector: The vector to search for.
            query_text: Text to search for. Will be embedded if `embedding_function` is configured.
            k: The number of nearest neighbors to retrieve.
            filters: Dictionary of metadata filters (see README for syntax).
            filter_sql: Raw SQL WHERE clause string. Overrides `filters`.
            select_columns: List of column names to retrieve. None retrieves all non-vector columns.
            include_vector: Whether to include the 'vector' field in results.

        Returns:
            List[Dict[str, Any]]: Matching memory entries, with '_distance' field.
        """
        if not self.table:
            raise InitializationError("Table not initialized.")

        if query_vector is None and query_text is None:
            raise ValueError("Either 'query_vector' or 'query_text' must be provided.")
        if query_vector is None and query_text and not self.embedding_function:
            raise EmbeddingError("'query_text' provided, but no embedding_function is configured.")
        if query_vector and len(query_vector) != self._vector_dimension:
            raise SchemaError(
                f"Query vector has dimension {len(query_vector)}, but table expects {self._vector_dimension}"
            )

        # If query_text is given and EF is present, LanceDB's search() handles embedding.
        # If query_vector is given, it's used directly.
        search_obj = self.table.search(query=query_text, vector=query_vector).limit(k)

        final_filter_sql = filter_sql
        if not final_filter_sql and filters:
            final_filter_sql = build_filter_sql(filters)

        if final_filter_sql:
            search_obj = search_obj.where(final_filter_sql)

        # Column selection logic
        actual_select = None
        if select_columns:
            actual_select = list(set(select_columns))  # Use set to avoid duplicates
            if include_vector and "vector" not in actual_select:
                actual_select.append("vector")
        elif include_vector:  # select_columns is None, but we want vector
            # To select all + vector, we don't pass select() if LanceDB returns vector by default
            # Or, get all schema fields and pass them.
            # For now, if include_vector=True and select_columns=None, we don't explicitly select,
            # relying on LanceDB to return it. We'll handle exclusion below.
            pass

        if actual_select:
            search_obj = search_obj.select(actual_select)

        try:
            results_df = search_obj.to_df()
            results_list = results_df.to_dict(orient="records")

            # Post-process to exclude vector if not requested and not explicitly selected
            if not include_vector and (not select_columns or "vector" not in select_columns):
                for res in results_list:
                    res.pop("vector", None)

            if self.update_last_accessed_on_query and results_list:
                accessed_ids = [res["id"] for res in results_list if "id" in res]
                if accessed_ids:
                    self._update_last_accessed(accessed_ids)
                    # Update timestamp_last_accessed in the returned results for immediate reflection
                    current_time = time.time()
                    for res in results_list:
                        if res.get("id") in accessed_ids and (
                            not select_columns or "timestamp_last_accessed" in select_columns or select_columns is None
                        ):
                            res["timestamp_last_accessed"] = current_time
            return results_list
        except Exception as e:
            raise QueryError(f"Query execution failed. Filter SQL was: '{final_filter_sql or 'N/A'}'. Error: {e}")

    def get_by_id(self, entry_id: str, select_columns: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Retrieves a memory entry by its ID."""
        if not self.table:
            raise InitializationError("Table not initialized.")

        filter_sql = f"id = '{str(entry_id)}'"  # Ensure entry_id is string for SQL
        try:
            query_obj = self.table.search().where(filter_sql).limit(1)

            # Handle column selection similar to query method
            actual_select = None
            if select_columns:
                actual_select = list(set(select_columns))
                # vector handling not usually primary for get_by_id, but consistent
                if "vector" not in actual_select and not self.update_last_accessed_on_query:  # Simple case
                    pass  # if vector not in select, it wont be fetched by select()

            if actual_select:
                query_obj = query_obj.select(actual_select)

            results_df = query_obj.to_df()

            if not results_df.empty:
                entry_data = results_df.to_dict(orient="records")[0]

                # Exclude vector if not explicitly requested by select_columns (if select_columns was used)
                if select_columns and "vector" not in select_columns and "vector" in entry_data:
                    entry_data.pop("vector")
                elif (
                    not select_columns and "vector" in entry_data
                ):  # Default: exclude vector for get_by_id unless include_vector becomes an arg
                    entry_data.pop("vector")

                if self.update_last_accessed_on_query:
                    self._update_last_accessed([entry_id])
                    if not select_columns or "timestamp_last_accessed" in select_columns:
                        entry_data["timestamp_last_accessed"] = time.time()
                return entry_data
            return None
        except Exception as e:
            print(f"Warning: Could not retrieve by ID '{entry_id}'. Error: {e}")
            return None

    def delete(self, entry_id: Optional[str] = None, filter_sql: Optional[str] = None) -> int:
        """
        Deletes memory entries by ID or by a SQL filter.
        One of entry_id or filter_sql must be provided.

        Returns:
            int: Number of attempted deletions (1 if entry_id, or based on pre-query if filter_sql).
                 LanceDB delete itself does not return a count of deleted rows.
                 This method aims to provide a best-effort count.
        """
        if not self.table:
            raise InitializationError("Table not initialized.")
        if not entry_id and not filter_sql:
            raise ValueError("Either entry_id or filter_sql must be provided for deletion.")

        final_filter = filter_sql
        if entry_id:
            safe_entry_id = str(entry_id).replace("'", "''")  # Basic SQL escape
            id_filter = f"id = '{safe_entry_id}'"
            final_filter = f"({id_filter}) AND ({filter_sql})" if filter_sql else id_filter

        if not final_filter:  # Should not happen due to initial check
            raise ValueError("A valid filter condition for deletion is required.")

        # To provide a count, we would ideally query how many match the filter first.
        # This adds an extra operation.
        num_matching = 0
        try:
            # This select can be slow on very large tables with complex filters
            matching_df = self.table.search().where(final_filter).select(["id"]).to_df()
            num_matching = len(matching_df)

            if num_matching > 0:
                self.table.delete(final_filter)
                print(f"Attempted to delete {num_matching} entries matching filter: {final_filter}")
            else:
                print(f"No entries found matching filter for deletion: {final_filter}")
            return num_matching
        except Exception as e:
            raise OperationError(f"Failed to delete memory entry/entries with filter '{final_filter}': {e}")

    def count(self, filters: Optional[Dict[str, Any]] = None, filter_sql: Optional[str] = None) -> int:
        """Counts entries, optionally filtered."""
        if not self.table:
            raise InitializationError("Table not initialized.")

        final_filter_sql = filter_sql
        if not final_filter_sql and filters:
            final_filter_sql = build_filter_sql(filters)

        try:
            if final_filter_sql:
                # LanceDB search().to_df() can be used, but select minimal data.
                # Using count_rows() if available and supports filter, else fallback.
                if hasattr(self.table, "count_rows") and callable(self.table.count_rows):
                    # As of lancedb 0.6.0, count_rows takes a filter string.
                    return self.table.count_rows(filter=final_filter_sql)
                else:  # Fallback for older versions or if count_rows doesn't take filter
                    df_ids = self.table.search().where(final_filter_sql).select(["id"]).to_df()
                    return len(df_ids)
            return len(self.table)  # Total count in table (uses Table.__len__)
        except Exception as e:
            raise QueryError(f"Failed to count entries. Filter: '{final_filter_sql or 'None'}'. Error: {e}")

    def prune_memories(
        self,
        max_age_seconds: Optional[int] = None,
        min_importance_score: Optional[float] = None,
        max_last_accessed_seconds: Optional[int] = None,
        custom_filter_sql: Optional[str] = None,
        filter_logic: str = "AND",  # "AND" or "OR" for combining criteria from args
        dry_run: bool = False,
    ) -> int:
        """Prunes memories based on age, importance, last access, or custom SQL."""
        if not self.table:
            raise InitializationError("Table not initialized.")
        if not any([max_age_seconds, min_importance_score is not None, max_last_accessed_seconds, custom_filter_sql]):
            print("Warning: No pruning criteria specified for prune_memories.")
            return 0

        built_conditions = []
        current_time = time.time()

        if max_age_seconds is not None:
            built_conditions.append(f"timestamp_created < {current_time - max_age_seconds}")
        if min_importance_score is not None:  # Prune if importance IS LESS THAN this
            built_conditions.append(f"(importance_score < {min_importance_score} OR importance_score IS NULL)")
        if max_last_accessed_seconds is not None:  # Prune if not accessed recently OR never accessed
            built_conditions.append(
                f"(timestamp_last_accessed < {current_time - max_last_accessed_seconds} OR timestamp_last_accessed IS NULL)"
            )

        combined_args_filter = ""
        if built_conditions:
            combined_args_filter = f" {filter_logic.upper()} ".join(f"({cond})" for cond in built_conditions)

        final_pruning_filter = combined_args_filter
        if custom_filter_sql:
            if final_pruning_filter:
                final_pruning_filter = f"({final_pruning_filter}) AND ({custom_filter_sql})"
            else:
                final_pruning_filter = custom_filter_sql

        if not final_pruning_filter:
            print("Warning: Pruning filter construction resulted in an empty filter.")
            return 0

        print(f"Pruning filter ({'DRY RUN' if dry_run else 'EXECUTE'}): {final_pruning_filter}")

        try:
            # Get count of items to be pruned
            # Use count method for efficiency if it supports filters well
            num_to_prune = self.count(filter_sql=final_pruning_filter)

            if not dry_run and num_to_prune > 0:
                deleted_count = self.delete(filter_sql=final_pruning_filter)  # Use internal delete
                # The delete method now attempts to return a count.
                print(f"Successfully pruned {deleted_count} memories (matched {num_to_prune}).")
                return deleted_count  # Or num_to_prune if delete's count is less reliable
            elif dry_run:
                print(f"[DRY RUN] Would prune {num_to_prune} memories.")

            return num_to_prune
        except Exception as e:
            raise OperationError(f"Failed to prune memories with filter '{final_pruning_filter}': {e}")

    def reflect_and_summarize(
        self,
        summarization_callback: Callable[[List[Dict], str], Tuple[str, List[float]]],
        query_vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        k_to_retrieve: int = 10,
        query_filters: Optional[Dict[str, Any]] = None,
        query_filter_sql: Optional[str] = None,
        new_memory_type: str = "reflection_summary",
        new_memory_source: str = "reflection_process",
        new_memory_tags: Optional[List[str]] = None,
        new_memory_importance: Optional[float] = None,
        new_memory_metadata: Optional[Dict[str, Any]] = None,
        delete_original_memories: bool = False,
    ) -> Optional[str]:
        """
        Facilitates agent reflection: retrieves memories, uses callback for summarization, stores summary.

        Args:
            summarization_callback: fn(retrieved_memories: List[Dict], topic: str) -> (summary_content, summary_vector).
            ... (other args as documented in README)

        Returns:
            ID of the new summary memory, or None on failure.
        """
        if not self.table:
            raise InitializationError("Table not initialized.")
        if not (query_vector or query_text):
            raise ValueError("Either query_vector or query_text must be provided for reflection.")

        topic_for_callback = query_text if query_text else "vector_based_reflection_topic"

        original_memories = self.query(
            query_vector=query_vector,
            query_text=query_text,
            k=k_to_retrieve,
            filters=query_filters,
            filter_sql=query_filter_sql,
            include_vector=True,  # Callback might need vectors or full data
        )

        if not original_memories:
            print(f"No memories found for reflection on topic: {topic_for_callback}")
            return None

        try:
            summary_content, summary_vector = summarization_callback(original_memories, topic_for_callback)
        except Exception as e:
            print(f"Error in summarization_callback for topic '{topic_for_callback}': {e}")
            return None

        if (
            not summary_content or summary_vector is None
        ):  # summary_vector can be empty list if dimension is 0 (unlikely)
            print("Summarization callback did not return valid content or vector.")
            return None
        if len(summary_vector) != self._vector_dimension:
            raise SchemaError(
                f"Summary vector from callback has dimension {len(summary_vector)}, expected {self._vector_dimension}"
            )

        original_memory_ids = [mem["id"] for mem in original_memories if "id" in mem]

        new_memory_data = {
            "content": summary_content,
            "vector": summary_vector,
            "type": new_memory_type,
            "source": new_memory_source,
            "tags": new_memory_tags or [],
            "importance_score": new_memory_importance,
            "metadata": new_memory_metadata or {},
            "related_memories": original_memory_ids,  # Link summary to originals
        }
        new_memory_data = {k: v for k, v in new_memory_data.items() if v is not None}  # Clean Nones

        new_summary_id = self.add(**new_memory_data)

        if delete_original_memories and original_memory_ids:
            ids_sql_list = ", ".join([f"'{str(eid)}'" for eid in original_memory_ids])
            delete_filter = f"id IN ({ids_sql_list})"
            try:
                num_deleted = self.delete(filter_sql=delete_filter)
                print(f"Deleted {num_deleted} original memories after summarization.")
            except Exception as e:
                print(f"Warning: Failed to delete original memories (IDs: {original_memory_ids}): {e}")
        return new_summary_id

    def list_tables(self) -> List[str]:
        """Lists all tables in the database connection."""
        return self.db.table_names()

    def close(self):
        """
        Closes the database connection if applicable.
        For LanceDB, connection objects are typically lightweight and might not require explicit closing.
        This method is provided for API completeness if underlying DB patterns change.
        """
        # self.db (LanceDBConnection) doesn't have an explicit .close() as of lancedb 0.6.0.
        # Operations are generally committed immediately.
        print(
            "AgentVectorDB: LanceDB connection does not require explicit close. Resources are managed by the library."
        )

    def __len__(self):
        """Returns the total number of entries in the current table."""
        if not self.table:
            return 0
        return len(self.table)  # Uses Table.__len__ which should be efficient
