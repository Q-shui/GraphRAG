"""Read-only inspection and normalisation for external aluminum QA JSONL."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


class AluminumQADataset:
    REQUIRED = ("question", "reference_answer")

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def rows(self) -> list[dict[str, Any]]:
        valid = []
        with self.path.open(encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                row = json.loads(line)
                missing = [key for key in self.REQUIRED if not row.get(key)]
                if missing:
                    raise ValueError(f"{self.path}:{line_no} missing {','.join(missing)}")
                row["_line"] = line_no
                valid.append(row)
        return valid

    def audit(self) -> dict[str, Any]:
        rows = self.rows()
        def count(name): return dict(sorted(Counter(str(row.get(name)) for row in rows).items()))
        return {"path": str(self.path), "records": len(rows), "question_ids_unique": len({row.get("question_id") or row.get("pool_id") for row in rows}) == len(rows),
                "evidence_status": count("evidence_status"), "expert_review_status": count("expert_review_status"),
                "candidate_status": count("candidate_status"), "primary_type": count("primary_type"),
                "with_source_ids": sum(bool(row.get("source_ids")) for row in rows),
                "with_evidence_locations": sum(bool(row.get("evidence_locations")) for row in rows)}

    def graph_eval_view(self) -> list[dict[str, Any]]:
        """Stable external-QA interface; preserves evidence/review fields."""
        return [{"id": row.get("question_id") or row.get("pool_id"), "question": row["question"],
                 "answer": row["reference_answer"], "key_answer_points": row.get("key_answer_points", []),
                 "evidence_locations": row.get("evidence_locations"), "source_ids": row.get("source_ids"),
                 "evidence_status": row.get("evidence_status"), "expert_review_status": row.get("expert_review_status"),
                 "question_type": row.get("primary_type"), "conditions": row.get("applicable_conditions")}
                for row in self.rows()]
