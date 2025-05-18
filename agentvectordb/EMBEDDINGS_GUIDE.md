## Choosing and Using Embedding Models with AgentVectorDB

AgentVectorDB is designed to work with a variety of text embedding models. The quality of your embeddings directly impacts how well your AI agents can understand context, retrieve relevant memories, and perform reasoning tasks. This guide will help you understand your options and how to integrate them.

### What are Embeddings?

In simple terms, embedding models convert text (or other data types) into a list of numbers called a "vector." These vectors capture the semantic meaning of the text. Texts with similar meanings will have vectors that are "close" to each other in a multi-dimensional space. AgentVectorDB uses these vectors to find the most relevant memories for your agent's current needs.

### Why Your Choice of Embedding Model Matters

*   **Quality of Understanding:** Better models produce embeddings that more accurately capture nuances, leading to more relevant search results.
*   **Performance (Speed):** Some models are faster to generate embeddings than others.
*   **Resource Consumption:** Larger models typically require more RAM and computational power (CPU/GPU).
*   **Cost:** API-based models have per-use costs, while local models have infrastructure costs.
*   **Domain Specificity:** General-purpose models work well for many tasks, but highly specialized domains might benefit from domain-specific or fine-tuned models.
*   **Multilingual Needs:** If your agent needs to handle multiple languages, you'll need a multilingual model.

AgentVectorDB uses LanceDB under the hood, which has excellent support for integrating various embedding models, especially through its `EmbeddingFunctionRegistry` for models compatible with the `sentence-transformers` library and popular API-based models.

### How to Integrate Embedding Functions with AgentVectorDB

When you create an `AgentMemoryCollection` using `AgentVectorDBStore`, you'll pass an `embedding_function` instance:

```python
from agentvectordb import AgentVectorDBStore
# ... import or define your embedding function (ef) ...

store = AgentVectorDBStore(db_path="./my_agent_data")
my_collection = store.get_or_create_collection(
    name="my_memories",
    embedding_function=ef, # Your chosen embedding function instance
    # vector_dimension might be inferred if ef has ndims(), otherwise provide it
)
```

### Popular Embedding Model Options

Here are some recommended embedding models suitable for production, categorized into local/open-source and API-based:

#### 1. Local / Open-Source Models (Self-Hosted)

These models run on your own infrastructure, giving you data privacy and control. They are often used via the `sentence-transformers` library.

*   **Using LanceDB's `EmbeddingFunctionRegistry` (Recommended for `sentence-transformers`)**
    LanceDB makes it easy to use many `sentence-transformers` models:

    ```python
    from lancedb.embeddings import EmbeddingFunctionRegistry

    registry = EmbeddingFunctionRegistry.get_instance()

    # Example: all-MiniLM-L6-v2 (Fast, good baseline)
    # Dimension: 384
    ef_minilm = registry.get("sentence-transformers").create(name="all-MiniLM-L6-v2")
    # collection_minilm = store.get_or_create_collection(name="minilm_mem", embedding_function=ef_minilm)


    # Example: all-mpnet-base-v2 (High quality, general purpose)
    # Dimension: 768
    ef_mpnet = registry.get("sentence-transformers").create(name="sentence-transformers/all-mpnet-base-v2")
    # collection_mpnet = store.get_or_create_collection(name="mpnet_mem", embedding_function=ef_mpnet)


    # Example: BAAI/bge-large-en-v1.5 (State-of-the-art, may need query instructions)
    # Dimension: 1024
    ef_bge = registry.get("sentence-transformers").create(name="BAAI/bge-large-en-v1.5")
    # collection_bge = store.get_or_create_collection(name="bge_mem", embedding_function=ef_bge)
    # For BGE, you might prepend "Represent this sentence for searching relevant passages: " to your queries
    # when calling `collection.query(query_text="Represent this... " + your_actual_query)`
    # or create a custom wrapper (see below).
    ```

*   **Custom Wrapper for Local Models (e.g., for Instructor or advanced BGE usage)**
    If you need more control (like specific instruction formatting for Instructor or BGE models), you can create a custom embedding function class inheriting from `agentvectordb.embeddings.BaseEmbeddingFunction`.

    ```python
    from agentvectordb.embeddings import BaseEmbeddingFunction
    from sentence_transformers import SentenceTransformer # pip install sentence-transformers

    class CustomBGEWrapper(BaseEmbeddingFunction):
        def __init__(self, model_name="BAAI/bge-base-en-v1.5", 
                     doc_instruction="", 
                     query_instruction="Represent this query for retrieving relevant documents: "):
            self.model = SentenceTransformer(model_name)
            self.doc_instruction = doc_instruction
            self.query_instruction = query_instruction
            self._dimension = self.model.get_sentence_embedding_dimension()

        def source_column(self) -> str:
            return "content" # The field in MemoryEntrySchema containing text to embed

        def ndims(self) -> int:
            return self._dimension

        def generate(self, texts: list[str], is_query: bool = False) -> list[list[float]]:
            # For documents, just embed. For queries, prepend instruction.
            # This simple wrapper assumes `is_query` might be passed by a modified query method.
            # LanceDB's default EF integration might not pass `is_query`.
            # A more robust way is to have separate methods or ensure the query text is pre-formatted.
            
            # For simple document embedding by LanceDB on add:
            if not is_query:
                 texts_to_embed = [self.doc_instruction + text for text in texts]
            else: # This part would be called manually when forming a query vector
                 texts_to_embed = [self.query_instruction + text for text in texts]
            
            return self.model.encode(texts_to_embed, normalize_embeddings=True).tolist()

        # You would likely call this manually for queries:
        # query_vector = ef_custom_bge.generate(["my search query"], is_query=True)[0]
        # results = collection.query(query_vector=query_vector, k=5)

    # ef_custom_bge = CustomBGEWrapper()
    # collection_custom_bge = store.get_or_create_collection(name="custom_bge_mem", embedding_function=ef_custom_bge)
    ```

#### 2. API-based Models (Cloud Services)

These are convenient and often offer state-of-the-art performance but involve API costs and data transfer.

*   **OpenAI Embeddings (e.g., `text-embedding-3-small`)**
    *   Requires an OpenAI API key (usually set as `OPENAI_API_KEY` environment variable).
    *   `text-embedding-3-small` (Dimension: 1536 default, can be reduced) is recommended over older `text-embedding-ada-002`.

    ```python
    from lancedb.embeddings import EmbeddingFunctionRegistry
    registry = EmbeddingFunctionRegistry.get_instance()

    # Ensure OPENAI_API_KEY environment variable is set
    # ef_openai = registry.get("openai").create(name="text-embedding-ada-002") # Older model
    ef_openai_3_small = registry.get("openai").create(name="text-embedding-3-small")
    # collection_openai = store.get_or_create_collection(name="openai_mem", embedding_function=ef_openai_3_small)

    # To use reduced dimensions with text-embedding-3 models (saves storage and can be faster):
    # ef_openai_3_small_512d = registry.get("openai").create(name="text-embedding-3-small", dim=512)
    # collection_openai_512d = store.get_or_create_collection(name="openai_mem_512d", embedding_function=ef_openai_3_small_512d, vector_dimension=512)
    ```

*   **Cohere Embeddings (e.g., `embed-english-v3.0`)**
    *   Requires a Cohere API key.
    *   Cohere models benefit from specifying `input_type` (`search_document` for storage, `search_query` for queries).

    ```python
    from lancedb.embeddings import EmbeddingFunctionRegistry
    # Check if Cohere is directly in LanceDB's registry (it often is)
    # registry = EmbeddingFunctionRegistry.get_instance()
    # ef_cohere = registry.get("cohere").create(api_key="YOUR_COHERE_KEY", model_name="embed-english-v3.0")
    # When using Cohere EF from LanceDB registry, it typically handles input_type automatically based on context.

    # If creating a custom Cohere wrapper (for more control or if not in registry):
    # import cohere # pip install cohere
    # from agentvectordb.embeddings import BaseEmbeddingFunction
    # class MyCohereEF(BaseEmbeddingFunction):
    #     def __init__(self, api_key: str, model_name="embed-english-v3.0"):
    #         self.co = cohere.Client(api_key)
    #         self.model_name = model_name
    #         # Determine ndims from model, e.g., embed-english-v3.0 is 1024
    #         self._ndims = 1024
    #
    #     def source_column(self) -> str: return "content"
    #     def ndims(self) -> int: return self._ndims
    #
    #     def generate(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
    #         # For storing documents
    #         response = self.co.embed(texts=texts, model=self.model_name, input_type=input_type)
    #         return [emb for emb in response.embeddings]
    #
    #     def generate_query_embedding(self, query_text: str) -> list[float]:
    #         # For querying
    #         response = self.co.embed(texts=[query_text], model=self.model_name, input_type="search_query")
    #         return response.embeddings[0]
    #
    # my_cohere_ef = MyCohereEF(api_key="YOUR_COHERE_API_KEY")
    # collection_cohere = store.get_or_create_collection(name="cohere_mem", embedding_function=my_cohere_ef)
    # query_vec = my_cohere_ef.generate_query_embedding("my agent query")
    # results = collection_cohere.query(query_vector=query_vec, k=3)
    ```

*   **Google Vertex AI Embeddings (e.g., `textembedding-gecko`)**
    *   Requires Google Cloud setup and authentication.
    *   LanceDB has Vertex AI integration.

    ```python
    from lancedb.embeddings import EmbeddingFunctionRegistry
    registry = EmbeddingFunctionRegistry.get_instance()

    # Requires gcloud auth login and GOOGLE_APPLICATION_CREDENTIALS or similar setup
    # ef_vertex = registry.get("vertexai").create(
    #    project_id="your-gcp-project-id",
    #    location="your-gcp-region" # e.g., "us-central1"
    #    # model_name defaults to a gecko version
    # )
    # collection_vertex = store.get_or_create_collection(name="vertex_mem", embedding_function=ef_vertex)
    ```

### Key Considerations When Choosing a Model:

1.  **Task Appropriateness:**
    *   **General Semantic Search:** `all-mpnet-base-v2`, OpenAI `text-embedding-3-small`, Cohere `embed-english-v3.0`, BGE models.
    *   **Speed-Critical/Resource-Constrained:** `all-MiniLM-L6-v2`.
    *   **Multilingual:** `paraphrase-multilingual-mpnet-base-v2`, Cohere `embed-multilingual-v3.0`.
    *   **Need for Specific Task/Domain Adaptation:** Instructor models, or fine-tuning an open-source model (advanced).

2.  **Cost:**
    *   **Local Models:** Upfront compute setup (CPU/GPU) and maintenance. No per-call inference cost.
    *   **API Models:** Pay-as-you-go per token or per call. Can be simpler to start but costs can add up.

3.  **Performance & Latency:**
    *   API calls introduce network latency. Local models can be faster if on powerful hardware but slower on modest hardware.
    *   Larger models (e.g., `-large` or `-xl` variants) are generally slower than `-base` or `-small` variants.

4.  **Data Privacy:**
    *   Local models keep your data on your infrastructure.
    *   API models involve sending your data to the cloud provider.

5.  **Vector Dimensionality:**
    *   Higher dimensions can sometimes capture more nuance but increase storage size and can sometimes make ANN search slightly slower or require more memory.
    *   Newer models like OpenAI's `text-embedding-3-*` allow you to choose a lower dimensionality, which can be a good trade-off.

6.  **Benchmarking:**
    *   Always try to test a few candidate models on a sample of *your own data* and typical agent queries to see what works best for your specific use case.
    *   The [MTEB (Massive Text Embedding Benchmark)](https://huggingface.co/spaces/mteb/leaderboard) is a great resource for comparing models on standard tasks.

### Where to Find More Models:

*   **Hugging Face Model Hub:** The primary place for `sentence-transformers` compatible models. Search for "sentence similarity," "sentence embeddings."
*   **LanceDB Documentation:** Often lists explicitly supported models or easy integrations.
*   **Provider Documentation:** OpenAI, Cohere, Google Cloud AI Platform for their respective offerings.

By providing an `embedding_function` to your `AgentMemoryCollection`, AgentVectorDB handles the process of generating vectors when you `add()` text content and when you `query()` using `query_text`. If you provide raw vectors, ensure they match the `vector_dimension` expected by the collection.
