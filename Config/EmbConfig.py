from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from pydantic import field_validator, model_validator

from Core.Utils.YamlModel import YamlModel


class EmbeddingType(Enum):
    OPENAI = "openai"
    HF = "hf"
    OLLAMA = "ollama"


class EmbeddingConfig(YamlModel):
    """Option for Embedding.

    Examples:
    ---------
    """

    api_type: Optional[EmbeddingType] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None

    model: Optional[str] = None
    cache_folder: Optional[str] = None
    embed_batch_size: Optional[int] = None
    dimensions: Optional[int] = None  # output dimension of embedding model
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_allow_remote: bool = False
    timeout: int = 600
    max_retries: int = 2
    max_input_characters: Optional[int] = None

    @field_validator("api_type", mode="before")
    @classmethod
    def check_api_type(cls, v):
        if v == "":
            return None
        return v

    @model_validator(mode="after")
    def validate_ollama_settings(self):
        if self.api_type != EmbeddingType.OLLAMA:
            return self
        if self.api_key not in ["", None]:
            raise ValueError("embedding.api_key must be omitted in native Ollama mode")
        parsed = urlparse(self.ollama_host)
        is_loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("embedding.ollama_host must be an absolute HTTP(S) URL")
        if not self.ollama_allow_remote and not is_loopback:
            raise ValueError("Native Ollama only permits a loopback ollama_host unless ollama_allow_remote=true")
        if not self.model:
            raise ValueError("embedding.model is required in native Ollama mode")
        return self
