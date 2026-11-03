"""Read-only adapter for the modern-aluminum V2 OCR corpus.

The adapter never rewrites the corpus.  It turns each source extraction chunk
into the project input shape while retaining the complete source record in
``TextChunk.metadata``.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REQUIRED = ("chunk_id", "page_id", "chapter_id", "text", "source_image")


@dataclass(frozen=True)
class AluminumChunk:
    document_id: str
    chunk_id: str
    page_id: str
    chapter_id: str
    content: str
    title: str
    metadata: dict[str, Any]

    def graph_document(self) -> dict[str, Any]:
        return {"prechunked": True, "document_id": self.document_id, "chunk_id": self.chunk_id,
                "content": self.content, "title": self.title, "metadata": self.metadata}


class ModernAluminumDataset:
    def __init__(self, corpus_dir: str | Path):
        self.corpus_dir = Path(corpus_dir)
        self.path = self.corpus_dir / "data" / "modern_aluminum_v2_extraction_chunks.jsonl"
        if not self.path.exists():
            raise FileNotFoundError(f"Extraction chunks not found: {self.path}")
        self.invalid_records: list[dict[str, Any]] = []

    def iter_chunks(self, chapters: Iterable[str] | None = None, ids: Iterable[str] | None = None,
                    review_status: Iterable[str] | None = None, limit: int | None = None) -> Iterable[AluminumChunk]:
        wanted_chapters, wanted_ids = set(chapters or []), set(ids or [])
        wanted_status = set(review_status or [])
        accepted = 0
        with self.path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    self.invalid_records.append({"line": line_no, "reason": f"invalid_json: {exc.msg}"})
                    continue
                missing = [key for key in REQUIRED if not record.get(key)]
                if missing:
                    self.invalid_records.append({"line": line_no, "reason": "missing:" + ",".join(missing)})
                    continue
                if wanted_chapters and record["chapter_id"] not in wanted_chapters:
                    continue
                if wanted_ids and record["chunk_id"] not in wanted_ids:
                    continue
                if wanted_status and record.get("review_status") not in wanted_status:
                    continue
                metadata = dict(record)
                content = metadata.pop("text")
                document_id = f"{record['chapter_id']}:{record['page_id']}"
                yield AluminumChunk(document_id, record["chunk_id"], record["page_id"], record["chapter_id"],
                                    content, record.get("chapter_file", record["chapter_id"]), metadata)
                accepted += 1
                if limit is not None and accepted >= limit:
                    return

    def graph_documents(self, **filters) -> list[dict[str, Any]]:
        return [chunk.graph_document() for chunk in self.iter_chunks(**filters)]

    def audit(self) -> dict[str, Any]:
        records = list(self.iter_chunks())
        ids = Counter(item.chunk_id for item in records)
        text_sources = Counter(item.content for item in records)
        lengths = sorted(len(item.content) for item in records)
        pages_path = self.corpus_dir / "data" / "modern_aluminum_v2_pages.jsonl"
        manifest_path = self.corpus_dir / "build_manifest.json"
        page_records = []
        if pages_path.exists():
            for line in pages_path.read_text(encoding="utf-8").splitlines():
                try: page_records.append(json.loads(line))
                except json.JSONDecodeError: pass
        page_ids = {item.get("page_id") for item in page_records}
        unresolved_images = [item.chunk_id for item in records if not (self.corpus_dir / str(item.metadata.get("source_image", ""))).exists()]
        try: manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        except json.JSONDecodeError: manifest = {"error": "invalid_manifest_json"}
        risky = {"empty": 0, "formula_or_table_marker": 0, "control_characters": 0}
        for item in records:
            risky["empty"] += not bool(item.content.strip())
            risky["formula_or_table_marker"] += bool(re.search(r"[=≈≤≥]|\b(?:Na|Al|Ca|Mg|KF|AlF)\w*\b", item.content))
            risky["control_characters"] += bool(re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", item.content))
        return {"source": str(self.path), "valid_records": len(records), "invalid_records": self.invalid_records,
                "field_presence": {key: sum(bool(item.metadata.get(key) if key != "text" else item.content) for item in records) for key in REQUIRED},
                "duplicate_chunk_ids": sorted(key for key, count in ids.items() if count > 1),
                "duplicate_text_groups": sum(count > 1 for count in text_sources.values()),
                "text_chars": {"min": lengths[0] if lengths else 0, "max": lengths[-1] if lengths else 0, "total": sum(lengths)},
                "chapters_in_chunks": len({item.chapter_id for item in records}), "pages_file_records": len(page_records),
                "chunk_pages_missing_from_pages_file": sorted({item.page_id for item in records if item.page_id not in page_ids}),
                "source_images_resolvable_relative_to_corpus": len(records) - len(unresolved_images), "source_images_unresolved_chunk_count": len(unresolved_images),
                "risk_markers": risky, "manifest_counts": {key: manifest.get(key) for key in ("chapters", "pages", "chunks", "quality_flag_counts", "limitations")}}


class ModernAluminumRAGDataset:
    """Main.py-compatible corpus + QA view for the modern-aluminum project.

    Unlike ``RAGQueryDataset`` this deliberately has no dependency on
    ``Corpus.json`` / ``Question.json``.  The supplied candidate question pool
    is read-only and retains review/evidence fields in every output row.
    """
    def __init__(self, corpus_dir: str | Path, qa_file: str | Path | None = None):
        from Data.AluminumQADataset import AluminumQADataset
        self.corpus = ModernAluminumDataset(corpus_dir)
        root = Path(corpus_dir)
        self.qa_path = Path(qa_file) if qa_file else root / "unified_candidate_pool.jsonl"
        self.questions = AluminumQADataset(self.qa_path).graph_eval_view() if self.qa_path.exists() else []

    def get_corpus(self) -> list[dict[str, Any]]:
        return self.corpus.graph_documents()

    def __len__(self) -> int:
        return len(self.questions)

    def __getitem__(self, index: int) -> dict[str, Any]:
        return dict(self.questions[index])

    def audit(self) -> dict[str, Any]:
        return self.corpus.audit()
        records = list(self.iter_chunks())
        ids = Counter(item.chunk_id for item in records)
        text_sources = Counter(item.content for item in records)
        lengths = sorted(len(item.content) for item in records)
        pages_path = self.corpus_dir / "data" / "modern_aluminum_v2_pages.jsonl"
        manifest_path = self.corpus_dir / "build_manifest.json"
        page_records: list[dict[str, Any]] = []
        if pages_path.exists():
            with pages_path.open(encoding="utf-8") as handle:
                for line in handle:
                    try:
                        page_records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        page_ids = {item.get("page_id") for item in page_records}
        chapters = {item.chapter_id for item in records}
        unresolved_images = [item.chunk_id for item in records if not (self.corpus_dir / str(item.metadata.get("source_image", ""))).exists()]
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                manifest = {"error": "invalid_manifest_json"}
        risky = {"empty": 0, "formula_or_table_marker": 0, "control_characters": 0}
        for item in records:
            if not item.content.strip(): risky["empty"] += 1
            if re.search(r"[=≈≤≥]|\b(?:Na|Al|Ca|Mg|KF|AlF)\w*\b", item.content): risky["formula_or_table_marker"] += 1
            if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", item.content): risky["control_characters"] += 1
        return {
            "source": str(self.path), "valid_records": len(records), "invalid_records": self.invalid_records,
            "field_presence": {key: sum(bool(item.metadata.get(key) if key != "text" else item.content) for item in records)
                               for key in REQUIRED},
            "duplicate_chunk_ids": sorted(key for key, count in ids.items() if count > 1),
            "duplicate_text_groups": sum(1 for count in text_sources.values() if count > 1),
            "text_chars": {"min": lengths[0] if lengths else 0, "max": lengths[-1] if lengths else 0,
                           "total": sum(lengths)},
            "chapters_in_chunks": len(chapters), "pages_file_records": len(page_records),
            "chunk_pages_missing_from_pages_file": sorted({item.page_id for item in records if item.page_id not in page_ids}),
            # Paths are intentionally checked relative to the corpus only; an
            # unresolved path is reported, never silently deleted or rewritten.
            "source_images_resolvable_relative_to_corpus": len(records) - len(unresolved_images),
            "source_images_unresolved_chunk_count": len(unresolved_images),
            "risk_markers": risky,
            "manifest_counts": {key: manifest.get(key) for key in ("chapters", "pages", "chunks", "quality_flag_counts", "limitations")},
        }
