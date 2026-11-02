"""Mock-only regression tests for post-build retrieval/query compatibility."""

import asyncio
from types import SimpleNamespace
import unittest

from Core.Query.BaseQuery import BaseQuery
from Core.Retriever.CommunityRetriever import CommunityRetriever


class FakeReports:
    async def get_by_ids(self, identifiers):
        return [
            {
                "report_string": "community report",
                "report_json": {"rating": 1},
                # Match the schema currently written by LeidenCommunity:
                # occurrence is top-level, not nested under community_info.
                "occurrence": 1,
            }
            for _ in identifiers
        ]


class FakeCommunity:
    def __init__(self):
        self.community_schema = {
            "level-1": SimpleNamespace(level=1, occurrence=2),
            "level-3": SimpleNamespace(level=3, occurrence=1),
        }
        self.community_reports = FakeReports()


class FakeLLM:
    def __init__(self):
        self.calls = []

    async def aask(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"points": []}


class DummyQuery(BaseQuery):
    async def _retrieve_relevant_contexts(self, **kwargs):
        return ""

    async def generation_summary(self, query, context):
        return ""

    async def generation_qa(self, query, context):
        return ""


class QueryContextCompatibilityTests(unittest.TestCase):
    def test_community_retriever_uses_query_config_for_level_and_limits(self):
        query_config = SimpleNamespace(
            level=2,
            global_max_consider_community=512,
            global_min_community_rating=0,
            local_max_token_for_community_report=100,
            local_community_single_one=False,
        )
        retriever = CommunityRetriever(
            config=SimpleNamespace(), query_config=query_config, community=FakeCommunity()
        )
        results = asyncio.run(retriever.find_relevant_community_by_level())
        self.assertEqual(len(results), 1)

    def test_global_map_requests_json_and_handles_oversized_report(self):
        query = DummyQuery.__new__(DummyQuery)
        query.config = SimpleNamespace(global_max_token_for_community_report=300)
        query.llm = FakeLLM()
        report = "long " * 1000
        result = asyncio.run(query._map_global_communities("question", [{
            "report_string": report,
            "report_json": {"rating": 1},
            "community_info": {"occurrence": 1},
        }]))
        self.assertEqual(result, [[]])
        self.assertEqual(query.llm.calls[0][1]["format"], "json")

    def test_json_object_accepts_native_dict_and_legacy_text(self):
        self.assertEqual(BaseQuery._json_object({"points": []}, "test"), {"points": []})
        self.assertEqual(BaseQuery._json_object('{"points": []}', "test"), {"points": []})


if __name__ == "__main__":
    unittest.main()
