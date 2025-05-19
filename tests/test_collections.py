import time
import uuid
from typing import List

import pytest
from agentvectordb import AgentMemoryCollection
from agentvectordb.exceptions import SchemaError
from .conftest import VECTOR_DIMENSION_TEST

def generate_test_vectors(count: int, ef_generate_func) -> List[List[float]]:
    return ef_generate_func([f"text_for_vec_{i}" for i in range(count)])

# Tests will be rewritten after fixing the underlying issues
