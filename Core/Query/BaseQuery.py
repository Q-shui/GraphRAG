import asyncio
from abc import ABC, abstractmethod
from Core.Retriever.MixRetriever import MixRetriever
from typing import Any
from Core.Prompt import GraphPrompt, QueryPrompt
from Core.Common.Utils import clean_str, prase_json_from_response, truncate_list_by_token_size, \
    truncate_str_by_token_size, list_to_quoted_csv_string
from Core.Common.Logger import logger


class BaseQuery(ABC):
    def __init__(self, config, retriever_context):
        self._retriever = MixRetriever(retriever_context)
        self.config = config
        self.llm = self._retriever.llm

    @abstractmethod
    async def _retrieve_relevant_contexts(self, **kwargs):
        pass

    async def query(self, query):
        context = await self._retrieve_relevant_contexts(query=query)
        response = None
        if self.config.query_type == "summary":
            response = await self.generation_summary(query, context)
        elif self.config.query_type == "qa":
            response = await self.generation_qa(query, context)
        else:
            logger.error("Invalid query type")
        return response

    @staticmethod
    def _json_object(response, stage: str) -> dict:
        """Normalize native Ollama and legacy provider JSON return contracts."""
        if isinstance(response, dict):
            return response
        if not isinstance(response, str):
            raise TypeError(f"{stage} returned {type(response).__name__}, expected JSON object or string")
        return prase_json_from_response(response)

    @abstractmethod
    async def generation_summary(self, query, context):
        pass

    @abstractmethod
    async def generation_qa(self, query, context):
        pass

    async def extract_query_entities(self, query):
        entities = []
        try:
            ner_messages = GraphPrompt.NER.format(user_input=query)

            response_content = await self.llm.aask(ner_messages, format="json")
            entities = self._json_object(response_content, "query entity extraction")

            if 'named_entities' not in entities:
                entities = []
            else:
                entities = entities['named_entities']

            entities = [clean_str(p) for p in entities]
        except Exception as e:
            logger.error('Error in Retrieval NER: {}'.format(e))

        return entities

    async def extract_query_keywords(self, query, mode="low"):
        kw_prompt = QueryPrompt.KEYWORDS_EXTRACTION.format(query=query)
        result = await self.llm.aask(kw_prompt, format="json")
        keywords = None
        keywords_data = self._json_object(result, "query keyword extraction")
        if mode == "low":
            keywords = keywords_data.get("low_level_keywords", [])
            keywords = ", ".join(keywords)
        elif mode == "high":
            keywords = keywords_data.get("high_level_keywords", [])
            keywords = ", ".join(keywords)
        elif mode == "hybrid":
            low_level = keywords_data.get("low_level_keywords", [])
            high_level = keywords_data.get("high_level_keywords", [])
            keywords = [low_level, high_level]

        return keywords

    async def _map_global_communities(
            self,
            query: str,
            communities_data
    ):

        # TODO: support other type of context filter
        community_groups = []
        # Leave room for CSV labels and the global-map instruction.  The
        # configured budget has already been clamped to Ollama's context
        # window by Config; this local reserve prevents a single report from
        # consuming that entire budget.
        report_budget = max(1, self.config.global_max_token_for_community_report - 256)
        while len(communities_data):
            this_group = truncate_list_by_token_size(
                communities_data,
                key=lambda x: x["report_string"],
                max_token_size=report_budget,
            )
            if not this_group:
                # Without advancing, an oversized first report causes an
                # infinite loop.  Preserve a bounded prefix instead.
                oversized = dict(communities_data[0])
                oversized["report_string"] = truncate_str_by_token_size(
                    oversized["report_string"], report_budget
                )
                this_group = [oversized]
            community_groups.append(this_group)
            communities_data = communities_data[len(this_group):]

        async def _process(community_truncated_datas: list[Any]) -> dict:
            communities_section_list = [["id", "content", "rating", "importance"]]
            for i, c in enumerate(community_truncated_datas):
                communities_section_list.append(
                    [
                        i,
                        c["report_string"],
                        c["report_json"].get("rating", 0),
                        c['community_info']['occurrence'],
                    ]
                )
            community_context = list_to_quoted_csv_string(communities_section_list)
            sys_prompt_temp = QueryPrompt.GLOBAL_MAP_RAG_POINTS
            sys_prompt = sys_prompt_temp.format(context_data=community_context)

            response = await self.llm.aask(
                query,
                system_msgs=[sys_prompt],
                format="json",
            )
            data = self._json_object(response, "global community map")
            points = data.get("points", [])
            if not isinstance(points, list):
                logger.warning("Global community map returned a non-list points field; ignoring that group")
                return []
            return points

        logger.info(f"Grouping to {len(community_groups)} groups for global search")
        responses = await asyncio.gather(*[_process(c) for c in community_groups])

        return responses
