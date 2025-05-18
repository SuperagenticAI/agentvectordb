from typing import List

import numpy as np


class BaseEmbeddingFunction:
    def source_column(self) -> str:
        raise NotImplementedError

    def ndims(self) -> int:
        raise NotImplementedError

    def generate(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def __call__(self, texts: List[str]) -> List[List[float]]:
        return self.generate(texts)


class DefaultTextEmbeddingFunction(BaseEmbeddingFunction):
    """
    A placeholder/example text embedding function for AgentVectorDB.
    Uses pseudo-random vectors for demonstration and testing.
    Replace with a robust model (e.g., Sentence Transformers) for real applications.
    """

    def __init__(self, model_name_or_path: str = "mock_default_model", dimension: int = 64):
        self._model_name = model_name_or_path
        self._dimension = dimension
        # print(f"Initialized Mock DefaultTextEmbeddingFunction (model: {self._model_name}, dim: {self._dimension})")

    def source_column(self) -> str:
        return "content"

    def ndims(self) -> int:
        return self._dimension

    def generate(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        # print(f"DefaultTextEmbeddingFunction: Generating mock embeddings for {len(texts)} texts.")
        embeddings = []
        for i, text_item in enumerate(texts):
            # Ensure text_item is a string for len()
            current_text = str(text_item) if text_item is not None else ""
            seed = len(current_text) + i  # Simple seed for some variation
            np.random.seed(seed)
            embeddings.append(np.random.rand(self._dimension).astype(np.float32).tolist())
        return embeddings
