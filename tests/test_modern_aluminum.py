import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from Core.AluminumKG.CandidatePipeline import CandidateExtractor, export_candidate_graph
from Data.ModernAluminumDataset import ModernAluminumDataset

try:
    from Core.Chunk.DocChunk import DocChunk
    from Core.Storage.ChunkKVStorage import ChunkKVStorage
    CHUNK_DEPS_AVAILABLE = True
except ModuleNotFoundError:
    CHUNK_DEPS_AVAILABLE = False


class Namespace:
    def __init__(self, root): self.root = Path(root)
    def get_save_path(self, name): return str(self.root / name)


class Tokenizer:
    def encode(self, text): return list(range(len(text)))


class ChunkConfig:
    chunk_method = "chunking_by_token_size"
    chunk_overlap_token_size = 0
    chunk_token_size = 100


class ModernAluminumTests(unittest.TestCase):
    def _corpus(self, root):
        data = Path(root) / "data"; data.mkdir(parents=True)
        rows = [
            {"chunk_id": "c1", "page_id": "p1", "chapter_id": "ch1", "chapter_file": "a.pdf", "text": "冰晶石影响氧化铝溶解度。", "source_image": "page1.png", "review_status": "unreviewed", "graph_ingestion_status": "candidate_only"},
            {"chunk_id": "c2", "page_id": "p2", "chapter_id": "ch1", "chapter_file": "a.pdf", "text": "冰晶石影响氧化铝溶解度。", "source_image": "page2.png", "review_status": "unreviewed", "graph_ingestion_status": "candidate_only"},
            {"chunk_id": "bad", "page_id": "p3", "chapter_id": "ch1", "text": "", "source_image": "x.png"},
        ]
        (data / "modern_aluminum_v2_extraction_chunks.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows), encoding="utf-8")

    def test_loader_keeps_identity_and_reports_invalid_records(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            self._corpus(root); ds = ModernAluminumDataset(root)
            chunks = list(ds.iter_chunks())
            self.assertEqual([x.chunk_id for x in chunks], ["c1", "c2"])
            self.assertNotEqual(chunks[0].page_id, chunks[1].page_id)
            self.assertEqual(ds.audit()["invalid_records"][0]["line"], 3)

    @unittest.skipUnless(CHUNK_DEPS_AVAILABLE, "core optional dependencies are not installed")
    def test_prechunked_persistence_keeps_metadata_and_duplicate_text_sources(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            self._corpus(root); docs = ModernAluminumDataset(root).graph_documents()
            namespace = Namespace(root); chunker = DocChunk(ChunkConfig(), Tokenizer(), namespace)
            asyncio.run(chunker.build_chunks(docs, force=True))
            first = asyncio.run(chunker._chunk.get_by_key("c1")); second = asyncio.run(chunker._chunk.get_by_key("c2"))
            self.assertEqual(first.metadata["page_id"], "p1")
            self.assertEqual(second.metadata["page_id"], "p2")
            loaded = ChunkKVStorage(namespace=namespace); self.assertTrue(asyncio.run(loaded.load_chunk()))
            self.assertEqual(asyncio.run(loaded.get_by_key("c2")).metadata["source_image"], "page2.png")

    def test_candidate_validation_and_evidence_export(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as root:
            self._corpus(root); chunk = next(ModernAluminumDataset(root).iter_chunks())
            raw = {"entities": [{"raw_name": "冰晶石", "entity_type": "物质和化合物"}], "relations": [
                {"subject": "冰晶石", "predicate": "影响", "object": "氧化铝溶解度", "evidence_text": "冰晶石影响氧化铝溶解度", "confidence": 0.3},
                {"subject": "冰晶石", "predicate": "导致", "object": "错误", "evidence_text": "不存在证据"}]}
            result = CandidateExtractor.validate(raw, chunk)
            self.assertTrue(result.relations[0]["evidence_verified"])
            self.assertFalse(result.relations[1]["evidence_verified"])
            counts = export_candidate_graph([result], Path(root) / "out")
            self.assertEqual(counts["relations"], 2)
            self.assertTrue((Path(root) / "out" / "review_queue.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
