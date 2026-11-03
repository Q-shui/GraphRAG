"""Structured candidate extraction and export for modern aluminum OCR.

This module intentionally does not mark model output as approved knowledge.
It is small enough to be used beside the existing GraphRAG methods and leaves
their graph structures untouched.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from Data.ModernAluminumDataset import AluminumChunk

PROMPT_VERSION = "modern-aluminum-candidate-v1"
ENTITY_TYPES = ["物质和化合物", "电解槽及设备部件", "工艺过程", "工艺参数", "物理化学性质", "工艺现象", "故障和异常", "控制或操作措施", "工艺条件", "其他"]
RELATIONS = ["包含或组成", "属于", "发生于", "影响", "促进", "抑制", "导致", "采用", "测量", "具有参数", "适用条件", "参与反应"]

PROMPT = """你是电解铝教材的候选知识抽取器。只依据给定 OCR 文本，不得补充常识。
返回一个 JSON 对象，键为 entities 和 relations。entities 中每项包含 raw_name, canonical_name,
entity_type, aliases；relations 中每项包含 subject, predicate, object, qualifiers, evidence_text,
confidence, quality_flags。entity_type 必须为：{types} 之一；predicate 必须为：{relations} 之一。
证据必须是原文连续短引；找不到可靠证据时返回空数组。OCR 模糊的数字、化学式、表格、公式或图示
必须在 quality_flags 中标明 needs_image_review，且不得擅自纠正。'影响'不等同于'导致'。
所有结果均为 candidate_only，绝不能输出 approved。

文本：
{text}
"""


def _normalise_evidence(value: str) -> str:
    return re.sub(r"\s+", "", value or "")


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    packed = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return prefix + hashlib.sha256(packed.encode("utf-8")).hexdigest()[:20]


@dataclass
class CandidateResult:
    chunk_id: str
    page_id: str
    chapter_id: str
    source_image: str
    entities: list[dict[str, Any]]
    relations: list[dict[str, Any]]
    failures: list[dict[str, str]]
    prompt_version: str = PROMPT_VERSION
    review_status: str = "candidate_only"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CandidateExtractor:
    def __init__(self, llm):
        self.llm = llm

    @staticmethod
    def validate(raw: Any, chunk: AluminumChunk) -> CandidateResult:
        failures: list[dict[str, str]] = []
        if not isinstance(raw, dict):
            raw = {}
            failures.append({"stage": "schema", "reason": "response_is_not_object"})
        entities: list[dict[str, Any]] = []
        names: set[str] = set()
        for value in raw.get("entities", []):
            if not isinstance(value, dict):
                failures.append({"stage": "entity", "reason": "not_object"}); continue
            name = value.get("canonical_name") or value.get("raw_name")
            if not isinstance(name, str) or not name.strip():
                failures.append({"stage": "entity", "reason": "missing_name"}); continue
            entity_type = value.get("entity_type", "其他")
            if entity_type not in ENTITY_TYPES:
                failures.append({"stage": "entity", "reason": "invalid_type"}); entity_type = "其他"
            item = {"entity_id": _stable_id("ent-", {"name": name.strip(), "type": entity_type}),
                    "raw_name": str(value.get("raw_name") or name).strip(), "canonical_name": name.strip(),
                    "entity_type": entity_type, "aliases": value.get("aliases") if isinstance(value.get("aliases"), list) else [],
                    "supporting_chunk_ids": [chunk.chunk_id], "review_status": "candidate_only"}
            if item["entity_id"] not in names:
                entities.append(item); names.add(item["entity_id"])
        relations: list[dict[str, Any]] = []
        for value in raw.get("relations", []):
            if not isinstance(value, dict):
                failures.append({"stage": "relation", "reason": "not_object"}); continue
            subject, predicate, obj, evidence = (value.get("subject"), value.get("predicate"), value.get("object"), value.get("evidence_text"))
            if not all(isinstance(x, str) and x.strip() for x in (subject, predicate, obj, evidence)):
                failures.append({"stage": "relation", "reason": "missing_required_field"}); continue
            if predicate not in RELATIONS:
                failures.append({"stage": "relation", "reason": "invalid_predicate"}); continue
            evidence_ok = _normalise_evidence(evidence) in _normalise_evidence(chunk.content)
            flags = value.get("quality_flags") if isinstance(value.get("quality_flags"), list) else []
            if not evidence_ok:
                flags = sorted(set(flags + ["evidence_not_found_needs_review"]))
                failures.append({"stage": "evidence", "reason": "evidence_not_in_chunk"})
            qualifiers = value.get("qualifiers") if isinstance(value.get("qualifiers"), dict) else {}
            relation = {"subject": subject.strip(), "predicate": predicate, "object": obj.strip(), "qualifiers": qualifiers,
                        "evidence_text": evidence, "evidence_chunk_id": chunk.chunk_id, "evidence_page_ids": [chunk.page_id],
                        "source_image": chunk.metadata.get("source_image"), "confidence": value.get("confidence"),
                        "quality_flags": flags, "evidence_verified": evidence_ok, "review_status": "candidate_only"}
            relation["relation_id"] = _stable_id("rel-", {k: relation[k] for k in ("subject", "predicate", "object", "evidence_chunk_id", "evidence_text")})
            relations.append(relation)
        return CandidateResult(chunk.chunk_id, chunk.page_id, chunk.chapter_id, str(chunk.metadata.get("source_image", "")), entities, relations, failures)

    async def extract(self, chunk: AluminumChunk) -> CandidateResult:
        prompt = PROMPT.format(types="、".join(ENTITY_TYPES), relations="、".join(RELATIONS), text=chunk.content)
        raw = await self.llm.aask(prompt, format="json")
        return self.validate(raw, chunk)


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    destination = Path(path); destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def export_candidate_graph(results: list[CandidateResult], output_dir: str | Path) -> dict[str, int]:
    """Export occurrence-level facts; same semantic triples never lose evidence."""
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    entities = [entity for result in results for entity in result.entities]
    relations = [relation for result in results for relation in result.relations]
    evidence = [{"relation_id": r["relation_id"], "chunk_id": r["evidence_chunk_id"], "page_ids": r["evidence_page_ids"],
                 "source_image": r["source_image"], "evidence_text": r["evidence_text"], "verified": r["evidence_verified"]}
                for r in relations]
    write_jsonl(out / "candidate_extractions.jsonl", [result.as_dict() for result in results])
    write_jsonl(out / "candidate_entities.jsonl", entities)
    write_jsonl(out / "candidate_relations.jsonl", relations)
    write_jsonl(out / "evidence_index.jsonl", evidence)
    write_jsonl(out / "review_queue.jsonl", [{"record_kind": "relation", "record_id": r["relation_id"], "review_status": "candidate_only",
                                                "decision": "", "reviewer": "", "note": ""} for r in relations])
    write_jsonl(out / "failures.jsonl", [{"chunk_id": result.chunk_id, **failure} for result in results for failure in result.failures])
    return {"chunks": len(results), "entities": len(entities), "relations": len(relations), "failures": sum(len(x.failures) for x in results)}


def load_checkpoint(path: str | Path) -> dict[str, CandidateResult]:
    """Load prior occurrence-level output for resumable runs.

    The checkpoint is only reusable when its run manifest fingerprint matches;
    that decision is made by the command layer, not guessed from chunk IDs.
    """
    source = Path(path)
    if not source.exists():
        return {}
    result: dict[str, CandidateResult] = {}
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            result[row["chunk_id"]] = CandidateResult(**row)
    return result
