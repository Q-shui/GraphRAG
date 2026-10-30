"""Native keyless Ollama embedding adapter used by all GraphRAG indexes."""

from __future__ import annotations

from typing import Optional

from llama_index.core.embeddings import BaseEmbedding
from pydantic import Field, PrivateAttr

from Core.Provider.OllamaClient import OllamaHttpClient, OllamaProtocolError


class NativeOllamaEmbedding(BaseEmbedding):
    """`/api/embed` implementation with batch-order and dimension validation."""

    model_name: str = Field(description="Ollama embedding model name")
    ollama_host: str = Field(default="http://127.0.0.1:11434")
    timeout: int = Field(default=600, ge=1)
    max_retries: int = Field(default=2, ge=0)
    allow_remote: bool = Field(default=False)
    expected_dimension: Optional[int] = Field(default=None, ge=1)
    max_input_characters: Optional[int] = Field(default=None, ge=1)
    _client: OllamaHttpClient = PrivateAttr()
    _observed_dimension: Optional[int] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        self._client = OllamaHttpClient(self.ollama_host, self.timeout, self.max_retries, self.allow_remote)

    @classmethod
    def class_name(cls) -> str:
        return "NativeOllamaEmbedding"

    def _validate_inputs(self, texts: list[str]) -> None:
        if not texts or any(not isinstance(text, str) for text in texts):
            raise ValueError("Ollama embedding input must be a non-empty list of strings")
        if self.max_input_characters is not None:
            oversized = [index for index, text in enumerate(texts) if len(text) > self.max_input_characters]
            if oversized:
                raise ValueError(f"Embedding input exceeds max_input_characters at indexes {oversized}")

    def _validate_response(self, response: dict, expected_count: int) -> list[list[float]]:
        vectors = response.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != expected_count:
            raise OllamaProtocolError(
                f"Ollama /api/embed returned {len(vectors) if isinstance(vectors, list) else 'invalid'} vectors for {expected_count} inputs"
            )
        result: list[list[float]] = []
        for vector in vectors:
            if not isinstance(vector, list) or not vector or not all(isinstance(value, (int, float)) for value in vector):
                raise OllamaProtocolError("Ollama /api/embed returned an invalid vector")
            result.append([float(value) for value in vector])
        dimensions = {len(vector) for vector in result}
        if len(dimensions) != 1:
            raise OllamaProtocolError("Ollama /api/embed returned mixed vector dimensions")
        dimension = dimensions.pop()
        expected = self.expected_dimension or self._observed_dimension
        if expected is not None and dimension != expected:
            raise OllamaProtocolError(f"Embedding dimension mismatch: expected {expected}, received {dimension}")
        self._observed_dimension = dimension
        return result

    def _payload(self, texts: list[str]) -> dict:
        self._validate_inputs(texts)
        return {"model": self.model_name, "input": texts}

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self._validate_response(self._client.post_json_sync("/api/embed", self._payload(texts)), len(texts))

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embeddings([text])[0]

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._get_text_embedding(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return (await self._aget_text_embeddings([text]))[0]

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return await self._aget_text_embedding(query)

    async def _aget_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return self._validate_response(await self._client.post_json("/api/embed", self._payload(texts)), len(texts))

    @property
    def embedding_metadata(self) -> dict:
        return {
            "backend": "ollama-native",
            "model": self.model_name,
            "host": self._client.host,
            "dimension": self._observed_dimension or self.expected_dimension,
        }

    @property
    def dimensions(self) -> int:
        """Compatibility with the existing FAISS index implementation."""
        dimension = self._observed_dimension or self.expected_dimension
        if dimension is None:
            raise OllamaProtocolError(
                "Embedding dimension is unknown before the first /api/embed response; "
                "do not create a FAISS index before embeddings have been generated."
            )
        return dimension
