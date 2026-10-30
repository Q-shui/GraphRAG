import re
import asyncio
import time
from collections import defaultdict
from typing import Union, List, Any
from Core.Graph.BaseGraph import BaseGraph
from Core.Common.Logger import logger
from Core.Common.Utils import (
    clean_str,
    split_string_by_multi_markers,
    is_float_regex
)
from Core.Schema.ChunkSchema import TextChunk
from Core.Schema.Message import Message
from Core.Prompt import GraphPrompt
from Core.Schema.EntityRelation import Entity, Relationship
from Core.Common.Constants import (
    DEFAULT_RECORD_DELIMITER,
    DEFAULT_COMPLETION_DELIMITER,
    DEFAULT_TUPLE_DELIMITER,
    DEFAULT_ENTITY_TYPES
)
from Core.Common.Memory import Memory
from Core.Storage.NetworkXStorage import NetworkXStorage


class RKGraph(BaseGraph):

    def __init__(self, config, llm, encoder):
        super().__init__(config, llm, encoder)
        self._graph = NetworkXStorage()

    @classmethod
    async def _handle_single_entity_extraction(self, record_attributes: list[str], chunk_key: str) -> Union[
        Entity, None]:

        if len(record_attributes) < 4 or record_attributes[0] != '"entity"':
            return None

        entity_name = clean_str(record_attributes[1])
        if not entity_name.strip():
            return None

        entity = Entity(
            entity_name=entity_name,
            entity_type=clean_str(record_attributes[2]),
            description=clean_str(record_attributes[3]),
            source_id=chunk_key
        )

        return entity

    async def _extract_entity_relationship(self, chunk_key_pair: tuple[str, TextChunk]):
        chunk_key, chunk_info = chunk_key_pair
        records = await self._extract_records_from_chunk(chunk_info)
        return await self._build_graph_from_records(records, chunk_key)

    async def _extract_entity_relationship_with_progress(
            self, index: int, chunk_key_pair: tuple[str, TextChunk]):
        """Extract one chunk and return compact telemetry for build progress.

        The extraction and record parsing paths are intentionally the same as
        ``_extract_entity_relationship``.  Only timing/counting is added.
        """
        chunk_key, _ = chunk_key_pair
        started_at = time.perf_counter()
        try:
            element = await self._extract_entity_relationship(chunk_key_pair)
        except Exception:
            logger.exception("[KG extraction] failed chunk={}/? id={}", index + 1, chunk_key)
            raise

        nodes, edges = element
        return index, element, len(nodes), len(edges), time.perf_counter() - started_at

    async def _build_graph(self, chunk_list: List[Any]):
        chunks = list(chunk_list)
        total = len(chunks)
        progress_interval = max(1, self.config.extraction_progress_interval)
        started_at = time.perf_counter()
        completed = 0
        extracted_nodes = 0
        extracted_edges = 0
        elements: list[Any] = [None] * total
        tasks = [
            asyncio.create_task(self._extract_entity_relationship_with_progress(index, chunk))
            for index, chunk in enumerate(chunks)
        ]
        logger.info(
            "[KG extraction] started chunks={} max_gleaning={} progress_interval={}",
            total, self.config.max_gleaning, progress_interval,
        )
        try:
            # ``as_completed`` only changes when progress is observed.  All
            # extraction tasks are still scheduled immediately, as they were
            # with gather(), and results are restored to input order before
            # graph merging to retain deterministic downstream behavior.
            for future in asyncio.as_completed(tasks):
                index, element, node_count, edge_count, chunk_elapsed = await future
                elements[index] = element
                completed += 1
                extracted_nodes += node_count
                extracted_edges += edge_count

                if completed % progress_interval == 0 or completed == total:
                    elapsed = time.perf_counter() - started_at
                    avg_seconds = elapsed / completed
                    eta_seconds = avg_seconds * (total - completed)
                    logger.info(
                        "[KG extraction] completed={}/{} ({:.1f}%) chunk_s={:.2f} "
                        "elapsed_s={:.1f} eta_s={:.1f} parsed_nodes={} parsed_edges={}",
                        completed, total, completed * 100 / total if total else 100.0,
                        chunk_elapsed, elapsed, eta_seconds, extracted_nodes, extracted_edges,
                    )
            # Build graph based on the extracted entities and triples
            await self.__graph__(elements)
        except Exception as e:
            logger.exception(f"Error building graph: {e}")
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            # Never let an extraction failure be persisted as an empty graph.
            raise
        finally:
            logger.info(
                "Constructing graph finished: completed={}/{} elapsed_s={:.1f}",
                completed, total, time.perf_counter() - started_at,
            )

    async def _extract_records_from_chunk(self, chunk_info: TextChunk):
        """
        Extract entity and relationship from chunk, which is used for the GraphRAG.
        Please refer to the following references:
        1. https://github.com/gusye1234/nano-graphrag
        2. https://github.com/HKUDS/LightRAG/tree/main
        """
        context = self._build_context_for_entity_extraction(chunk_info.content)
        prompt_template = GraphPrompt.ENTITY_EXTRACTION_KEYWORD if self.config.enable_edge_keywords else GraphPrompt.ENTITY_EXTRACTION
        prompt = prompt_template.format(**context)

        working_memory = Memory()

        working_memory.add(Message(content=prompt, role="user"))
        final_result = await self.llm.aask(prompt)
        working_memory.add(Message(content=final_result, role="assistant"))

        for glean_idx in range(self.config.max_gleaning):
            working_memory.add(Message(content=GraphPrompt.ENTITY_CONTINUE_EXTRACTION, role="user"))
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in working_memory.get())
            glean_result = await self.llm.aask(context)
            working_memory.add(Message(content=glean_result, role="assistant"))
            final_result += glean_result

            if glean_idx == self.config.max_gleaning - 1:
                break

            working_memory.add(Message(content=GraphPrompt.ENTITY_IF_LOOP_EXTRACTION, role="user"))
            context = "\n".join(f"{msg.sent_from}: {msg.content}" for msg in working_memory.get())
            if_loop_result = await self.llm.aask(context)
            if if_loop_result.strip().strip('"').strip("'").lower() != "yes":
                break
        working_memory.clear()
        return split_string_by_multi_markers(final_result, [
            DEFAULT_RECORD_DELIMITER, DEFAULT_COMPLETION_DELIMITER
        ])

    async def _build_graph_from_records(self, records: list[str], chunk_key: str):
        maybe_nodes, maybe_edges = defaultdict(list), defaultdict(list)

        for record in records:
            match = re.search(r"\((.*)\)", record)
            if match is None:
                continue

            record_attributes = split_string_by_multi_markers(match.group(1), [DEFAULT_TUPLE_DELIMITER])
            entity = await self._handle_single_entity_extraction(record_attributes, chunk_key)

            if entity is not None:
                maybe_nodes[entity.entity_name].append(entity)
                continue

            relationship = await self._handle_single_relationship_extraction(record_attributes, chunk_key)

            if relationship is not None:
                maybe_edges[(relationship.src_id, relationship.tgt_id)].append(relationship)

        return dict(maybe_nodes), dict(maybe_edges)

    async def _handle_single_relationship_extraction(self, record_attributes: list[str], chunk_key: str) -> Union[
        Relationship, None]:
        if len(record_attributes) < 5 or record_attributes[0] != '"relationship"':
            return None

        return Relationship(
            src_id=clean_str(record_attributes[1]),
            tgt_id=clean_str(record_attributes[2]),
            weight=float(record_attributes[-1]) if is_float_regex(record_attributes[-1]) else 1.0,
            description=clean_str(record_attributes[3]),
            source_id=chunk_key,
            keywords=clean_str(record_attributes[4]) if self.config.enable_edge_keywords else ""
        )

    @classmethod
    def _build_context_for_entity_extraction(self, content: str) -> dict:
        return dict(
            tuple_delimiter=DEFAULT_TUPLE_DELIMITER,
            record_delimiter=DEFAULT_RECORD_DELIMITER,
            completion_delimiter=DEFAULT_COMPLETION_DELIMITER,
            entity_types=",".join(DEFAULT_ENTITY_TYPES),
            input_text=content
        )
        
    @property
    def entity_metakey(self):
        return "entity_name"
