import os
import time  # Add this import
import lancedb
import pyarrow as pa
from datetime import datetime
from typing import Dict, Optional, Any, Type, List
from .collection import AgentMemoryCollection
from .schemas import MemoryEntrySchema
from .exceptions import InitializationError, OperationError

class AgentVectorDBStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        try:
            os.makedirs(self.db_path, exist_ok=True)
            self.db = lancedb.connect(self.db_path)
        except Exception as e:
            raise InitializationError(f"Failed to connect/init LanceDB at {self.db_path}: {e}")
        self._collections_cache: Dict[str, AgentMemoryCollection] = {}

    def get_or_create_collection(
        self, 
        name: str, 
        embedding_function: Optional[Any] = None,
        base_schema: Type[MemoryEntrySchema] = MemoryEntrySchema,
        vector_dimension: Optional[int] = None,
        update_last_accessed_on_query: bool = False,
        recreate: bool = False
    ) -> AgentMemoryCollection:
        try:
            vec_dim = vector_dimension or (embedding_function._dimension if hasattr(embedding_function, '_dimension') else 64)
            
            schema = pa.schema([
                ('id', pa.string()),
                ('content', pa.string()),
                ('vector', pa.list_(pa.float32(), vec_dim)),
                ('type', pa.string()),
                ('importance_score', pa.float32()),
                ('metadata', pa.struct([
                    ('source', pa.string()),
                    ('tags', pa.list_(pa.string())),
                    ('extra', pa.string())
                ])),
                ('created_at', pa.float64()),
                ('last_accessed_at', pa.float64())
            ])

            current_time = time.time()
            empty_data = [{
                'id': '', 
                'content': '',
                'vector': [0.0] * vec_dim,
                'type': '',
                'importance_score': 0.0,
                'metadata': {
                    'source': '',
                    'tags': [],
                    'extra': '{}'
                },
                'created_at': current_time,
                'last_accessed_at': current_time
            }]

            # Create or get the table - removed embedding config
            table = self.db.create_table(
                name=name,
                data=empty_data,
                schema=schema,
                mode="overwrite" if recreate else "create"
            )

            # Create vector index after table creation
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

        except Exception as e:
            raise OperationError(f"Failed to create/get collection '{name}': {e}")

        collection_instance = AgentMemoryCollection(
            self.db.open_table(name),
            name,
            embedding_function=embedding_function,
            base_schema=base_schema,
            vector_dimension=vector_dimension,
            update_last_accessed_on_query=update_last_accessed_on_query
        )

        return collection_instance

    def list_collections(self) -> list[str]:
        try:
            return self.db.table_names()
        except Exception as e:
            raise OperationError(f"Failed to list collections: {e}")

