"""Small, keyless clients for Ollama's native local HTTP API.

This module intentionally does not use the OpenAI-compatible Ollama endpoint.
It centralises host validation and transport so application code never embeds a
URL or can silently fall back to a cloud SDK.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import aiohttp


class OllamaError(RuntimeError):
    """Base error for a native Ollama request."""


class OllamaConnectionError(ConnectionError, OllamaError):
    """Ollama could not be reached at the configured local listener."""


class OllamaProtocolError(OllamaError):
    """Ollama returned an invalid, incomplete, or unexpected response."""


def normalize_ollama_host(host: str, allow_remote: bool = False) -> str:
    parsed = urlparse(host)
    loopback = {"127.0.0.1", "localhost", "::1"}
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Ollama host must be an absolute HTTP(S) URL")
    if not allow_remote and parsed.hostname not in loopback:
        raise ValueError("Ollama host must be loopback unless remote access is explicitly enabled")
    return host.rstrip("/")


class OllamaHttpClient:
    """Native JSON client with bounded retry and no authentication headers."""

    def __init__(self, host: str, timeout: int, max_retries: int, allow_remote: bool = False):
        self.host = normalize_ollama_host(host, allow_remote)
        self.timeout = timeout
        self.max_retries = max(0, max_retries)

    def _url(self, path: str) -> str:
        return urljoin(f"{self.host}/", path.lstrip("/"))

    @staticmethod
    def _decode(payload: bytes, url: str) -> dict[str, Any]:
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OllamaProtocolError(f"Ollama returned non-JSON data from {url}") from exc
        if not isinstance(decoded, dict):
            raise OllamaProtocolError(f"Ollama returned a non-object response from {url}")
        if decoded.get("error"):
            raise OllamaProtocolError(f"Ollama error: {decoded['error']}")
        return decoded

    async def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._url(path)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload) as response:
                        raw = await response.read()
                        if response.status >= 400:
                            detail = raw.decode("utf-8", errors="replace")[:500]
                            raise OllamaProtocolError(f"Ollama HTTP {response.status} from {url}: {detail}")
                        return self._decode(raw, url)
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_error = OllamaConnectionError(f"Cannot reach Ollama at {url}: {exc}")
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2 ** attempt, 4))
        raise last_error or OllamaConnectionError(f"Cannot reach Ollama at {url}")

    async def get_json(self, path: str) -> dict[str, Any]:
        """Read-only native endpoints such as `/api/tags` and `/api/ps`."""
        url = self._url(path)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        raw = await response.read()
                        if response.status >= 400:
                            detail = raw.decode("utf-8", errors="replace")[:500]
                            raise OllamaProtocolError(f"Ollama HTTP {response.status} from {url}: {detail}")
                        return self._decode(raw, url)
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                last_error = OllamaConnectionError(f"Cannot reach Ollama at {url}: {exc}")
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2 ** attempt, 4))
        raise last_error or OllamaConnectionError(f"Cannot reach Ollama at {url}")

    async def list_models(self) -> dict[str, Any]:
        return await self.get_json("/api/tags")

    async def running_models(self) -> dict[str, Any]:
        return await self.get_json("/api/ps")

    async def show_model(self, model: str) -> dict[str, Any]:
        return await self.post_json("/api/show", {"model": model})

    def post_json_sync(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._url(path)
        data = json.dumps(payload).encode("utf-8")
        request = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    return self._decode(response.read(), url)
            except HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                raise OllamaProtocolError(f"Ollama HTTP {exc.code} from {url}: {detail}") from exc
            except (URLError, TimeoutError) as exc:
                last_error = OllamaConnectionError(f"Cannot reach Ollama at {url}: {exc}")
                if attempt < self.max_retries:
                    import time
                    time.sleep(min(2 ** attempt, 4))
        raise last_error or OllamaConnectionError(f"Cannot reach Ollama at {url}")
