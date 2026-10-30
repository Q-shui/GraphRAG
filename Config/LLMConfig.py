#!/usr/bin/env python
# -*- coding: utf-8 -*-


from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from pydantic import field_validator, model_validator

from Core.Common.Constants import LLM_API_TIMEOUT, GRAPHRAG_ROOT
from Core.Utils.YamlModel import YamlModel


class LLMType(Enum):
    OPENAI = "openai"
    FIREWORKS = "fireworks"
    OPEN_LLM = "open_llm"
    OLLAMA = "ollama"  # /chat at ollama api
    OLLAMA_GENERATE = "ollama.generate"  # /generate at ollama api
    OLLAMA_EMBEDDINGS = "ollama.embeddings"  # /embeddings at ollama api
    OLLAMA_EMBED = "ollama.embed"  # /embed at ollama api
    OPENROUTER = "openrouter"
    BEDROCK = "bedrock"
    ARK = "ark"  # https://www.volcengine.com/docs/82379/1263482#python-sdk

    def __missing__(self, key):
        return self.OPENAI


class LLMConfig(YamlModel):
    """Option for LLM

    OpenAI: https://github.com/openai/openai-python/blob/main/src/openai/resources/chat/completions.py#L681
    Optional Fields in pydantic: https://docs.pydantic.dev/latest/migration/#required-optional-and-nullable-fields
    """

    # A local Ollama server authenticates by its loopback listener, not an API key.
    # Keep this optional so local mode never needs a real or placeholder key.
    api_key: Optional[str] = None
    api_type: LLMType = LLMType.OPENAI
    base_url: str = "https://api.openai.com/v1"
    api_version: Optional[str] = None

    model: Optional[str] = None  # also stands for DEPLOYMENT_NAME
    pricing_plan: Optional[str] = None  # Cost Settlement Plan Parameters.

    # For Cloud Service Provider like Baidu/ Alibaba
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    session_token: Optional[str] = None
    endpoint: Optional[str] = None  # for self-deployed model on the cloud

    # For Spark(Xunfei), maybe remove later
    app_id: Optional[str] = None
    api_secret: Optional[str] = None
    domain: Optional[str] = None

    # For Chat Completion
    max_token: int = 4096
    temperature: float = 0.0
    top_p: float = 1.0
    top_k: int = 0
    repetition_penalty: float = 1.0
    stop: Optional[str] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    best_of: Optional[int] = None
    n: Optional[int] = None
    stream: bool = False  # Default True
    seed: Optional[int] = None
    # https://cookbook.openai.com/examples/using_logprobs
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    timeout: int = 600
    context_length: Optional[int] = None  # Max input tokens

    # Native Ollama options.  They are deliberately separate from ``base_url``:
    # the latter remains the OpenAI-compatible endpoint setting used by legacy
    # cloud providers.
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_allow_remote: bool = False
    ollama_num_ctx: Optional[int] = None
    ollama_keep_alive: Optional[str] = None
    ollama_think: Optional[bool] = False
    # Native Ollama has no cloud cost log.  Keep lightweight request telemetry
    # enabled so long graph builds remain observable.
    ollama_log_requests: bool = True
    max_retries: int = 2

    # For Amazon Bedrock
    region_name: str = None

    # For Network
    proxy: Optional[str] = None
    max_concurrent:int  = 20 # Your concurrent number 
    # Cost Control
    calc_usage: bool = True

    # For Messages Control
    use_system_prompt: bool = True

    @model_validator(mode="after")
    def validate_backend_settings(self):
        if self.api_type == LLMType.OLLAMA:
            if self.api_key not in ["", None]:
                raise ValueError("llm.api_key must be omitted in native Ollama mode")
            parsed = urlparse(self.ollama_host)
            is_loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("llm.ollama_host must be an absolute HTTP(S) URL")
            if not self.ollama_allow_remote and not is_loopback:
                raise ValueError("Native Ollama only permits a loopback ollama_host unless ollama_allow_remote=true")
            if not self.model:
                raise ValueError("llm.model is required in native Ollama mode")
            return self

        if self.api_key in ["", None, "YOUR_API_KEY"]:
            repo_config_path = GRAPHRAG_ROOT / "Option/Config2.yaml"
            if repo_config_path.exists():
                raise ValueError(f"Please set your API key in {repo_config_path}")
            else:
                raise ValueError("Please set your API key in config2.yaml")
        return self

    @field_validator("timeout")
    @classmethod
    def check_timeout(cls, v):
        return v or LLM_API_TIMEOUT
