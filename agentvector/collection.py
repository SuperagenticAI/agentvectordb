import time
import uuid
from typing import List, Dict, Any, Optional, Type, Callable, Tuple

import lancedb
from lancedb.table import Table
from pydantic import BaseModel, ValidationError

from .schemas import MemoryEntrySchema, create_dynamic_memory_entry_schema
from .exceptions import (
    InitializationError, SchemaError, QueryError, OperationError, EmbeddingError
)

class AgentMemoryCollection:
    def __init__(
        self,
        table: Any,  # LanceDB table instance
        name: str,
        embedding_function: Optional[Any] = None,
        base_schema: Type[MemoryEntrySchema] = MemoryEntrySchema,
        vector_dimension: Optional[int] = None,
        update_last_accessed_on_query: bool = False
    ):
        if table is None:
            raise InitializationError("table (LanceDB Table) must be provided.")
            
        self.table = table
        self.name = name
        self.embedding_function = embedding_function
        self._schema = base_schema
        self.vector_dimension = vector_dimension
        self.update_last_accessed_on_query = update_last_accessed_on_query

        self._vector_dimension = vector_dimension
        if self.embedding_function and hasattr(self.embedding_function, 'ndims') and callable(self.embedding_function.ndims):
            ef_dim = self.embedding_function.ndims()
            if self._vector_dimension and self._vector_dimension != ef_dim:
                raise InitializationError(
                    f"Collection '{name}': Provided vector_dimension ({self._vector_dimension}) "
                    f"conflicts with embedding_function's dimension ({ef_dim})."
                )
            self._vector_dimension = ef_dim
        
        if not self._vector_dimension: # This will be an int if derived from EF or provided.
            raise InitializationError(
                 f"Collection '{name}': vector_dimension must be determined (from EF or explicitly provided)."
            )

        if not issubclass(base_schema, MemoryEntrySchema): # Check type, not instance
             raise SchemaError(f"Collection '{name}': base_schema must be a subclass of agentvector.schemas.MemoryEntrySchema.")
        self.BaseSchema = base_schema
        self.DynamicSchema = create_dynamic_memory_entry_schema(self.BaseSchema, self._vector_dimension)

    @property
    def schema(self) -> Type[BaseModel]: return self.DynamicSchema

    def _prepare_data_for_add(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        # Handle metadata
        metadata = {
            'source': data_dict.pop('source', ''),
            'tags': data_dict.pop('tags', []),
            'extra': '{}'
        }
        data_dict['metadata'] = metadata

        # Generate vector if needed
        if self.embedding_function and 'content' in data_dict:
            try:
                data_dict['vector'] = self.embedding_function.generate([data_dict['content']])[0]
            except Exception as e:
                raise OperationError(f"Failed to generate embedding: {e}")

        # Add timestamps as float
        current_time = time.time()
        data_dict.setdefault('created_at', current_time)
        data_dict.setdefault('last_accessed_at', current_time)
        
        # Generate UUID if id not provided
        data_dict.setdefault('id', str(uuid.uuid4()))
        
        # Set default values
        data_dict.setdefault('type', '')
        data_dict.setdefault('importance_score', 0.0)
        
        try:
            validated_data = self._schema(**data_dict)
            return validated_data.model_dump()
        except ValidationError as e:
            raise SchemaError(f"Col '{self.name}', ID '{data_dict.get('id', 'N/A')}': Validation failed: {e}")
        return data_dict

    def add(self, **kwargs: Any) -> str:
        if not self.table: raise InitializationError(f"Col '{self.name}': Table not init.")
        entry_data = self._prepare_data_for_add(kwargs.copy())
        try:
            self.table.add([entry_data]); return entry_data["id"]
        except Exception as e: raise OperationError(f"Col '{self.name}', ID '{entry_data.get('id')}': Add failed: {e}")

    def add_batch(self, entries: List[Dict[str, Any]]) -> List[str]:
        if not self.table: raise InitializationError(f"Col '{self.name}': Table not init.")
        if not entries: return []
        processed = [self._prepare_data_for_add(e.copy()) for e in entries]
        ids = [p["id"] for p in processed]
        try: self.table.add(processed); return ids
        except Exception as e: raise OperationError(f"Col '{self.name}': Batch add failed: {e}")

    def _update_last_accessed(self, entry_ids: List[str]):
        if not entry_ids or not self.table: return
        try:
            ids_sql = ", ".join([f"'{str(eid)}'" for eid in entry_ids])
            self.table.update(values={"timestamp_last_accessed": time.time()}, where=f"id IN ({ids_sql})")
        except Exception as e: print(f"Warn: Col '{self.name}': Failed timestamp update: {e}")

    def query(
        self,
        query_text: Optional[str] = None,
        query_vector: Optional[List[float]] = None,
        k: int = 5,
        filter_sql: Optional[str] = None,
        select_columns: Optional[List[str]] = None,
        include_vector: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Query the collection using semantic search.
        """
        try:
            if query_text and self.embedding_function and not query_vector:
                query_vector = self.embedding_function.generate([query_text])[0]

            if query_vector is not None:
                # Use LanceDB's search API for vector search
                search_obj = self.table.search(
                    query_vector,
                    vector_column_name="vector"
                ).limit(k)
            else:
                search_obj = self.table.search(
                    query=query_text,
                    columns=["content"]
                ).limit(k)

            if filter_sql:
                search_obj = search_obj.where(filter_sql)

            results = search_obj.to_list()

            if self.update_last_accessed_on_query and results:
                current_time = time.time()
                for result in results:
                    self.table.update(
                    f"id = '{result['id']}'",
                    {"last_accessed_at": current_time}
                )

            return results

        except Exception as e:
            raise OperationError(f"Query failed: {e}")

    def get_by_id(self, entry_id: str, select_columns: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        if not self.table: raise InitializationError(f"Col '{self.name}': Table not init.")
        safe_id = str(entry_id).replace("'", "''")
        try:
            q_obj = self.table.search().where(f"id = '{safe_id}'").limit(1)
            if select_columns: q_obj = q_obj.select(list(set(select_columns)))
            
            df = q_obj.to_df()
            if df.empty: return None
            data = df.to_dict(orient='records')[0]

            if not select_columns or ("vector" not in select_columns and "vector" in data): data.pop('vector', None)
            elif not select_columns and "vector" in data : data.pop('vector', None)


            if self.update_last_accessed_on_query:
                self._update_last_accessed([entry_id])
                if not select_columns or 'timestamp_last_accessed' in select_columns:
                    data['timestamp_last_accessed'] = time.time()
            return data
        except Exception as e: print(f"Warn: Col '{self.name}': Get ID '{entry_id}' fail. Err: {e}"); return None

    def delete(self, entry_id: Optional[str] = None, filter_sql: Optional[str] = None) -> int:
        if not self.table: raise InitializationError(f"Col '{self.name}': Table not init.")
        if not entry_id and not filter_sql: raise ValueError("Need entry_id or filter_sql for delete.")
        
        final_filter = filter_sql
        if entry_id:
            id_f = f"id = '{str(entry_id).replace("'", "''")}'"
            final_filter = f"({id_f}) AND ({filter_sql})" if filter_sql else id_f
        if not final_filter: raise ValueError("Valid delete filter required.")

        try:
            matched_df = self.table.search().where(final_filter).select(["id"]).to_df()
            num_matched = len(matched_df)
            if num_matched > 0: self.table.delete(final_filter)
            # else: print(f"Col '{self.name}': No entries for delete: {final_filter}") # Less verbose
            return num_matched
        except Exception as e: raise OperationError(f"Col '{self.name}': Delete fail for '{final_filter}': {e}")

    def count(self, filter_sql: Optional[str] = None) -> int:
        if not self.table: raise InitializationError(f"Col '{self.name}': Table not init.")
        try:
            if filter_sql:
                if hasattr(self.table, 'count_rows') and callable(self.table.count_rows):
                    return self.table.count_rows(filter=filter_sql)
                return len(self.table.search().where(filter_sql).select(["id"]).to_df())
            return len(self.table)
        except Exception as e: raise QueryError(f"Col '{self.name}': Count fail. Filter: '{filter_sql or 'N/A'}'. Err: {e}")

    def prune_memories(self, max_age_seconds: Optional[int]=None, min_importance_score: Optional[float]=None,
                       max_last_accessed_seconds: Optional[int]=None, filter_logic: str="AND",
                       custom_filter_sql_addon: Optional[str]=None, dry_run: bool=False) -> int:
        if not self.table: raise InitializationError(f"Col '{self.name}': Table not init.")
        if not any([max_age_seconds, min_importance_score is not None, max_last_accessed_seconds, custom_filter_sql_addon]):
            return 0
        
        conds, ts = [], time.time()
        if max_age_seconds is not None: conds.append(f"timestamp_created < {ts - max_age_seconds}")
        if min_importance_score is not None: conds.append(f"(importance_score < {min_importance_score} OR importance_score IS NULL)")
        if max_last_accessed_seconds is not None:
            conds.append(f"(timestamp_last_accessed < {ts - max_last_accessed_seconds} OR timestamp_last_accessed IS NULL)")
        
        main_filter = f" {filter_logic.upper()} ".join(f"({c})" for c in conds) if conds else ""
        final_filter = f"({main_filter}) AND ({custom_filter_sql_addon})" if main_filter and custom_filter_sql_addon \
                       else main_filter or custom_filter_sql_addon or ""
        if not final_filter: return 0
        
        # print(f"Col '{self.name}': Prune filter ({'DRY RUN' if dry_run else 'EXECUTE'}): {final_filter}") # Less verbose
        try:
            num_to_prune = self.count(filter_sql=final_filter)
            if not dry_run and num_to_prune > 0: return self.delete(filter_sql=final_filter)
            return num_to_prune
        except Exception as e: raise OperationError(f"Col '{self.name}': Prune fail for '{final_filter}': {e}")

    def __len__(self): return len(self.table) if self.table else 0