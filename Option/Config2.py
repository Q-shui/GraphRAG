#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from pydantic import BaseModel, model_validator
from Config import *
from Config.LLMConfig import LLMType
from Core.Common.Constants import GRAPHRAG_ROOT
from Core.Utils.YamlModel import YamlModel


class WorkingParams(BaseModel):
    """Working parameters"""

    working_dir: str = ""
    exp_name: str = ""
    data_root: str = ""
    dataset_name: str = ""


class Config(WorkingParams, YamlModel):
    """Configurations for our project"""

    # Key Parameters
    llm: LLMConfig
    exp_name: str = "default"
    # RAG Embedding
    embedding: EmbeddingConfig = EmbeddingConfig()

    # Basic Config
    use_entities_vdb: bool = True
    use_relations_vdb: bool = True  # Only set True for LightRAG
    use_subgraphs_vdb: bool = False  # Only set True for Medical-GraphRAG
    vdb_type: str = "vector"  # vector/colbert
    token_model: str = "gpt-3.5-turbo"
    
    
    # Chunking
    chunk: ChunkConfig = ChunkConfig()
    # chunk_token_size: int = 1200
    # chunk_overlap_token_size: int = 100
    # chunk_method: str = "chunking_by_token_size"
   
    llm_model_max_token_size: int = 32768
  
    use_entity_link_chunk: bool = True  # Only set True for HippoRAG and FastGraphRAG
    
    # Graph Config
    graph: GraphConfig = GraphConfig()
    
    # Retrieval Parameters
    retriever: RetrieverConfig = RetrieverConfig()


    # ColBert Option
    use_colbert: bool = True
    colbert_checkpoint_path: str = "/home/yingli/HippoRAG/exp/colbertv2.0"
    index_name: str = "nbits_2"
    similarity_max: float = 1.0
    # Graph Augmentation
    enable_graph_augmentation: bool = True

    # Query Config 
    query: QueryConfig = QueryConfig()

    @model_validator(mode="after")
    def clamp_ollama_context_budgets(self):
        """Keep upstream method YAML usable with a finite Ollama context window.

        The method files retain their paper/original budgets (often 16K or
        32K).  Native Ollama requests must not exceed the configured context,
        so only the effective runtime budget is clamped here.
        """
        if self.llm.api_type != LLMType.OLLAMA or not self.llm.ollama_num_ctx:
            return self

        safety_margin = 512
        generation_budget = self.llm.max_token or 0
        query_input_budget = max(1, self.llm.ollama_num_ctx - generation_budget - safety_margin)
        summary_input_budget = max(1, self.llm.ollama_num_ctx - self.graph.summary_max_tokens - safety_margin)
        self.graph.llm_model_max_token_size = min(self.graph.llm_model_max_token_size, summary_input_budget)
        self.query.global_max_token_for_community_report = min(
            self.query.global_max_token_for_community_report, query_input_budget
        )
        self.query.max_token_for_global_context = min(self.query.max_token_for_global_context, query_input_budget)
        self.retriever.max_token_for_global_context = min(
            self.retriever.max_token_for_global_context, query_input_budget
        )
        return self
  
    @classmethod
    def from_yaml_config(cls, path: str):
        """user config llm
        example:
        llm_config = {"api_type": "xxx", "api_key": "xxx", "model": "xxx"}
        gpt4 = Option.from_llm_config(llm_config)
        A = Role(name="A", profile="Democratic candidate", goal="Win the election", actions=[a1], watch=[a2], config=gpt4)
        """
        opt = parse(path)
        return Config(**opt)

    @classmethod
    def parse(cls, _path, dataset_name):
        """Load the repository baseline, then apply the selected method YAML.

        This intentionally does not read ``$HOME/Option/Config2.yaml``.  A
        single checkout is therefore self-contained and runs with the same
        configuration on every machine.
        """
        final = merge_dict([
            Config.read_yaml(GRAPHRAG_ROOT / "Option/Config2.yaml"),
            parse(_path),
        ])
        final["dataset_name"] = dataset_name
        final["data_root"] = _resolve_project_path(final["data_root"])
        final["working_dir"] = os.path.join(_resolve_project_path(final["working_dir"]), dataset_name)
        return Config(**final)
    
    @classmethod
    def default(cls):
        """Load the repository's self-contained local baseline."""
        return Config(**Config.read_yaml(GRAPHRAG_ROOT / "Option/Config2.yaml"))

    @property
    def extra(self):
        return self._extra

    @extra.setter
    def extra(self, value: dict):
        self._extra = value

    def get_openai_llm(self) -> Optional[LLMConfig]:
        """Get OpenAI LLMConfig by name. If no OpenAI, raise Exception"""
        if self.llm.api_type == LLMType.OPENAI:
            return self.llm
        return None
def parse(opt_path):
    with open(opt_path, mode='r') as f:
        return YamlModel.read_yaml(opt_path)


def _resolve_project_path(path: str) -> str:
    candidate = Path(path)
    return str(candidate if candidate.is_absolute() else (GRAPHRAG_ROOT / candidate).resolve())


def merge_dict(dicts: Iterable[Dict]) -> Dict:
    """Recursively merge dictionaries, with later values taking precedence."""
    result = {}
    for dictionary in dicts:
        for key, value in dictionary.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = merge_dict([result[key], value])
            else:
                result[key] = value
    return result


default_config = Config.default() # which is used in other files, only for LLM, embedding and save file.
