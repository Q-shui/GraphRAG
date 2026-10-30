"""Native asynchronous Ollama LLM provider for GraphRAG."""

from __future__ import annotations

import asyncio
from typing import Any

from Config.LLMConfig import LLMConfig, LLMType
from Core.Common.Constants import USE_CONFIG_TIMEOUT
from Core.Common.Logger import logger
from Core.Provider.BaseLLM import BaseLLM
from Core.Provider.LLMProviderRegister import register_provider
from Core.Provider.OllamaClient import OllamaHttpClient, OllamaProtocolError


@register_provider(LLMType.OLLAMA)
class OllamaLLM(BaseLLM):
    """Adapter for Ollama `/api/chat`; it never invokes a cloud provider."""

    def __init__(self, config: LLMConfig, client: OllamaHttpClient | None = None):
        self.config = config
        self.model = config.model
        self.pricing_plan = self.model
        self.cost_manager = None
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.client = client or OllamaHttpClient(
            config.ollama_host, config.timeout, config.max_retries, config.ollama_allow_remote
        )
        self.last_response_metadata: dict[str, Any] = {}

    def _options(self, max_tokens: int | None) -> dict[str, Any]:
        options: dict[str, Any] = {"temperature": self.config.temperature, "top_p": self.config.top_p}
        if self.config.top_k:
            options["top_k"] = self.config.top_k
        if self.config.repetition_penalty != 1.0:
            options["repeat_penalty"] = self.config.repetition_penalty
        if self.config.seed is not None:
            options["seed"] = self.config.seed
        if self.config.ollama_num_ctx:
            options["num_ctx"] = self.config.ollama_num_ctx
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        elif self.config.max_token:
            options["num_predict"] = self.config.max_token
        return options

    def _payload(self, messages: list[dict], max_tokens: int | None, output_format: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": self._options(max_tokens),
        }
        if self.config.ollama_keep_alive is not None:
            payload["keep_alive"] = self.config.ollama_keep_alive
        if self.config.ollama_think is not None:
            payload["think"] = self.config.ollama_think
        if output_format == "json":
            payload["format"] = "json"
        elif output_format != "text":
            raise ValueError(f"Unsupported Ollama output format: {output_format}")
        return payload

    def _extract_text(self, response: dict[str, Any]) -> str:
        message = response.get("message")
        if not isinstance(message, dict):
            raise OllamaProtocolError("Ollama /api/chat response has no message object")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise OllamaProtocolError("Ollama /api/chat returned an empty assistant response")
        self.last_response_metadata = {
            "model": response.get("model", self.model),
            "prompt_eval_count": response.get("prompt_eval_count"),
            "eval_count": response.get("eval_count"),
            "total_duration": response.get("total_duration"),
            "load_duration": response.get("load_duration"),
            "thinking": message.get("thinking"),
        }
        usage = {
            "prompt_tokens": response.get("prompt_eval_count", 0) or 0,
            "completion_tokens": response.get("eval_count", 0) or 0,
        }
        self._update_costs(usage, local_calc_usage=False)
        return content

    async def _achat_completion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT, max_tokens: int | None = None,
                                format: str = "text") -> dict[str, Any]:
        # Per-call timeout is supplied by BaseLLM; use a short-lived client only
        # if it differs from the configured value.
        client = self.client if timeout == self.config.timeout else OllamaHttpClient(
            self.config.ollama_host, timeout, self.config.max_retries, self.config.ollama_allow_remote
        )
        return await client.post_json("/api/chat", self._payload(messages, max_tokens, format))

    async def acompletion(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT, max_tokens: int | None = None):
        return await self._achat_completion(messages, timeout, max_tokens)

    async def _achat_completion_stream(self, messages: list[dict], timeout=USE_CONFIG_TIMEOUT,
                                       max_tokens: int | None = None, format: str = "text") -> str:
        # GraphRAG consumes complete strings.  Requesting a complete native response
        # preserves that contract without parsing an NDJSON stream incorrectly.
        return await self.acompletion_text(messages, stream=False, timeout=timeout, max_tokens=max_tokens, format=format)

    async def acompletion_text(self, messages: list[dict], stream: bool = False, timeout=USE_CONFIG_TIMEOUT,
                               max_tokens: int | None = None, format: str = "text") -> str:
        response = await self._achat_completion(messages, timeout, max_tokens, format)
        text = self._extract_text(response)
        if format == "json":
            # Reuse existing project validation/repair behavior, but never turn a
            # malformed response into an empty extraction silently.
            from Core.Common.Utils import prase_json_from_response
            parsed = prase_json_from_response(text)
            if not isinstance(parsed, dict):
                raise OllamaProtocolError("Ollama JSON response did not parse to an object")
            return parsed
        return text

    def ask(self, messages: list[dict], max_tokens: int | None = None, format: str = "text") -> str:
        """Synchronous native chat for scripts; GraphRAG itself uses `aask`."""
        response = self.client.post_json_sync("/api/chat", self._payload(messages, max_tokens, format))
        return self._extract_text(response)
