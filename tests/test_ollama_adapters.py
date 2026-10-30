"""Mock-only tests for the native Ollama adapters; no Ollama process is used."""

import asyncio
import unittest

from Config.EmbConfig import EmbeddingConfig, EmbeddingType
from Config.LLMConfig import LLMConfig, LLMType
from Core.Index.OllamaEmbedding import NativeOllamaEmbedding
from Core.Provider.OllamaApi import OllamaLLM
from Core.Provider.OllamaClient import OllamaProtocolError, normalize_ollama_host


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def post_json(self, path, payload):
        self.calls.append((path, payload))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    def post_json_sync(self, path, payload):
        self.calls.append((path, payload))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class OllamaAdapterTests(unittest.TestCase):
    def test_local_configs_need_no_key_and_reject_remote_host(self):
        llm = LLMConfig(api_type=LLMType.OLLAMA, model="qwen3:4b")
        embedding = EmbeddingConfig(api_type=EmbeddingType.OLLAMA, model="nomic-embed-text:latest")
        self.assertIsNone(llm.api_key)
        self.assertIsNone(embedding.api_key)
        with self.assertRaises(ValueError):
            LLMConfig(api_type=LLMType.OLLAMA, model="qwen3:4b", ollama_host="http://10.0.0.5:11434")
        with self.assertRaises(ValueError):
            normalize_ollama_host("https://example.invalid")

    def test_chat_uses_native_payload_and_preserves_thinking_as_metadata(self):
        client = FakeClient([{
            "model": "qwen3:4b", "message": {"role": "assistant", "content": "{\"named_entities\": []}", "thinking": "hidden"},
            "prompt_eval_count": 5, "eval_count": 3,
        }])
        llm = OllamaLLM(LLMConfig(api_type=LLMType.OLLAMA, model="qwen3:4b"), client=client)
        result = asyncio.run(llm.acompletion_text([{"role": "user", "content": "extract"}], format="json"))
        self.assertEqual(result, {"named_entities": []})
        path, payload = client.calls[0]
        self.assertEqual(path, "/api/chat")
        self.assertEqual(payload["model"], "qwen3:4b")
        self.assertEqual(payload["format"], "json")
        self.assertNotIn("api_key", payload)
        self.assertEqual(llm.last_response_metadata["thinking"], "hidden")

    def test_embedding_preserves_batch_order_and_enforces_dimension(self):
        adapter = NativeOllamaEmbedding(model_name="nomic-embed-text:latest", expected_dimension=3)
        client = FakeClient([{"embeddings": [[1, 0, 0], [0, 1, 0]]}])
        adapter._client = client
        result = adapter._get_text_embeddings(["first", "second"])
        self.assertEqual(result, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        self.assertEqual(client.calls[0][1]["input"], ["first", "second"])
        self.assertEqual(adapter.embedding_metadata["dimension"], 3)

    def test_embedding_rejects_bad_count_and_empty_chat(self):
        adapter = NativeOllamaEmbedding(model_name="nomic-embed-text:latest")
        adapter._client = FakeClient([{"embeddings": [[1, 0]]}])
        with self.assertRaises(OllamaProtocolError):
            adapter._get_text_embeddings(["one", "two"])
        llm = OllamaLLM(
            LLMConfig(api_type=LLMType.OLLAMA, model="qwen3:4b"),
            client=FakeClient([{"message": {"content": ""}}]),
        )
        with self.assertRaises(OllamaProtocolError):
            asyncio.run(llm.acompletion_text([{"role": "user", "content": "hello"}]))


if __name__ == "__main__":
    unittest.main()
