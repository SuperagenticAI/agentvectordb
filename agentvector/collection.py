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
        db_connection: lancedb.db.LanceDBConnection,
        name: str,
        base_schema: Type[MemoryEntrySchema] = MemoryEntrySchema,
        vector_dimension: Optional[int] = None,
        embedding_function: Optional[Any] = None,
        update_last_accessed_on_query: bool = False,
        recreate: bool = False
    ):
        if not db_connection:
            raise InitializationError("db_connection (LanceDBConnection) must be provided.")
        self.db = db_connection
        self.name = name
        self.embedding_function = embedding_function
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

        if recreate and self.name in self.db.table_names():
            try:
                self.db.drop_table(self.name)
                # print(f"Collection '{self.name}': Dropped existing table.") # Less verbose for tests
            except Exception as e:
                raise OperationError(f"Collection '{self.name}': Failed to drop table: {e}")

        self.table: Optional[Table] = None
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        try:
            if self.name not in self.db.table_names():
                # print(f"Collection '{self.name}': Creating new table with schema {self.DynamicSchema.__name__}.") # Less verbose for tests
                ef_config_list = None
                if self.embedding_function:
                    if hasattr(self.embedding_function, 'source_column') and \
                       hasattr(self.embedding_function, 'generate') and \
                       callable(self.embedding_function.source_column) and \
                       callable(self.embedding_function.generate) :
                        from lancedb.embeddings import EmbeddingFunctionConfig
                        try:
                            source_col_name = self.embedding_function.source_column()
                            ef_config_list = [
                                EmbeddingFunctionConfig(
                                    source_column=source_col_name,
                                    vector_column="vector",
                                    function=self.embedding_function
                                )
                            ]
                        except Exception as ef_conf_e:
                             print(f"Warning: Collection '{self.name}': Could not create EmbeddingFunctionConfig. {ef_conf_e}")
                    # else: # Less verbose for tests
                        # print(f"Warning: Collection '{self.name}': EF may not be fully compatible with LanceDB auto-config.")
                
                self.table = self.db.create_table(
                    self.name, schema=self.DynamicSchema,
                    embedding_functions=ef_config_list, mode="create"
                )
            else:
                self.table = self.db.open_table(self.name)
        except Exception as e:
            raise InitializationError(f"Collection '{self.name}': Failed to create/open table: {e}")

    @property
    def schema(self) -> Type[BaseModel]: return self.DynamicSchema

    def _prepare_data_for_add(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        if "id" not in data_dict or not data_dict["id"]: data_dict["id"] = str(uuid.uuid4())
        if "timestamp_created" not in data_dict: data_dict["timestamp_created"] = time.time()

        if "vector" in data_dict and data_dict["vector"] is not None:
            if len(data_dict["vector"]) != self._vector_dimension:
                raise SchemaError(f"Col '{self.name}', ID '{data_dict['id']}': Vec dim mismatch.")
        elif "vector" not in data_dict:
            if not self.embedding_function:
                raise EmbeddingError(f"Col '{self.name}', ID '{data_dict['id']}': No vector and no EF.")
            source_col = getattr(self.embedding_function, 'source_column', lambda: 'content')()
            if not data_dict.get(source_col):
                 raise EmbeddingError(f"Col '{self.name}', ID '{data_dict['id']}': No vector & EF source ('{source_col}') missing.")
        try:
            self.DynamicSchema.model_validate(data_dict)
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

    def query(self, query_vector: Optional[List[float]] = None, query_text: Optional[str] = None, k: int = 5,
              filter_sql: Optional[str] = None, select_columns: Optional[List[str]] = None,
              include_vector: bool = False) -> List[Dict[str, Any]]:
        if not self.table: raise InitializationError(f"Col '{self.name}': Table not init.")
        if query_vector is None and query_text is None: raise ValueError("Need query_vector or query_text.")
        if query_vector is None and query_text and not self.embedding_function:
            raise EmbeddingError(f"Col '{self.name}': query_text needs EF.")
        if query_vector and len(query_vector) != self._vector_dimension:
             raise SchemaError(f"Col '{self.name}': Query vec dim mismatch.")

        search_obj = self.table.search(query=query_text, vector=query_vector).limit(k)
        if filter_sql: search_obj = search_obj.where(filter_sql)
        
        actual_select = None
        if select_columns:
            actual_select = list(set(select_columns))
            if include_vector and "vector" not in actual_select: actual_select.append("vector")
        if actual_select: search_obj = search_obj.select(actual_select)

        try:
            results_list = search_obj.to_df().to_dict(orient='records')
            if not include_vector and (not select_columns or "vector" not in select_columns):
                for res in results_list: res.pop('vector', None)
            if self.update_last_accessed_on_query and results_list:
                accessed_ids = [r['id'] for r in results_list if 'id' in r]
                if accessed_ids:
                    self._update_last_accessed(accessed_ids)
                    ts = time.time()
                    for r in results_list:
                        if r.get('id') in accessed_ids and \
                           (not actual_select or 'timestamp_last_accessed' in actual_select):
                             r['timestamp_last_accessed'] = ts
            return results_list
        except Exception as e:
            raise QueryError(f"Col '{self.name}': Query fail. SQL: '{filter_sql or 'N/A'}'. Err: {e}")

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