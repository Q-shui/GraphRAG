import os
import json
from pathlib import Path
from abc import ABC, abstractmethod
from Core.Common.Utils import clean_storage
from Core.Common.Logger import logger
from Core.Schema.VdbResult import * 

class BaseIndex(ABC):
    def __init__(self, config):
        self.config = config
        self._index = None

    async def build_index(self, elements, meta_data, force=False):
        logger.info("Starting insert elements of the given graph into vector database")
 
        from_load = False
        if self.exist_index() and not force:
            logger.info("Loading index from the file {}".format(self.config.persist_path))
            self._validate_embedding_metadata()
            from_load = await self._load_index()
        else:
        
            self._index = self._get_index()
        if not from_load:
            # Note: When you successfully load the index from a file, you don't need to rebuild it.
            await self.clean_index()
            logger.info("Building index for input elements")
            await self._update_index(elements, meta_data)
            self._storage_index()
            self._write_embedding_metadata()
            logger.info("Index successfully built and stored.")
        logger.info("✅ Finished starting insert entities of the given graph into vector database")

    def exist_index(self):
        return os.path.exists(self.config.persist_path)

    @property
    def _embedding_metadata_path(self) -> Path:
        return Path(self.config.persist_path) / ".graphrag_embedding.json"

    def _embedding_metadata(self) -> dict:
        """Return a stable, key-free fingerprint of the embedding space."""
        embed_model = getattr(self.config, "embed_model", None)
        if embed_model is None:
            return {"backend": "none"}
        metadata = getattr(embed_model, "embedding_metadata", None)
        if isinstance(metadata, dict):
            return metadata
        return {
            "backend": f"{embed_model.__class__.__module__}.{embed_model.__class__.__name__}",
            "model": getattr(embed_model, "model_name", None),
            "dimension": getattr(embed_model, "dimensions", None),
        }

    def _validate_embedding_metadata(self) -> None:
        """Refuse to load a vector index from an unknown embedding space."""
        path = self._embedding_metadata_path
        if not path.exists():
            raise RuntimeError(
                f"Refusing to reuse index without embedding metadata: {path}. "
                "Choose a new index/output directory or rebuild explicitly."
            )
        with path.open("r", encoding="utf-8") as handle:
            stored = json.load(handle)
        current = self._embedding_metadata()
        for field in ("backend", "model", "dimension"):
            # A missing configured dimension is learned on the first real embed;
            # backend and model must still match before any old index is loaded.
            if current.get(field) is not None and stored.get(field) != current.get(field):
                raise RuntimeError(
                    f"Embedding metadata mismatch for {field}: index={stored.get(field)!r}, "
                    f"current={current.get(field)!r}. Use a new output directory."
                )

    def _write_embedding_metadata(self) -> None:
        path = self._embedding_metadata_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(self._embedding_metadata(), handle, ensure_ascii=False, indent=2, sort_keys=True)

    @abstractmethod
    async def retrieval(self, query, top_k):
        pass

    @abstractmethod
    def _get_index(self):
        pass

    @abstractmethod
    async def retrieval_batch(self, queries, top_k):
        pass

    @abstractmethod
    async def _update_index(self, elements, meta_data):
        pass

    @abstractmethod
    def _get_retrieve_top_k(self):
        return 10

    @abstractmethod
    def _storage_index(self):
        pass

    @abstractmethod
    async def _load_index(self) -> bool:
        pass

    async def similarity_score(self, object_q, object_d):
        return await self._similarity_score(object_q, object_d)

    
    async def _similarity_score(self, object_q, object_d):
        pass

    
    async def get_max_score(self, query):
        pass

    async def clean_index(self):
       clean_storage(self.config.persist_path)
       
    @abstractmethod
    async def retrieval_nodes(self, query, top_k, graph):
        pass


    async def retrieval_nodes_with_score_matrix(self, query_list, top_k, graph):
        pass
