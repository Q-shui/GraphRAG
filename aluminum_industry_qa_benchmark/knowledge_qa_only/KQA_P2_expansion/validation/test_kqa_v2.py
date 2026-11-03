import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = [json.loads(x) for x in (ROOT / "datasets/knowledge_qa_v2_candidates.jsonl").read_text(encoding="utf-8").splitlines() if x]
assert len(rows) == 33
assert len({r["question_id"] for r in rows}) == 33
assert sum(r.get("origin") == "v1_reverified" for r in rows) == 13
assert sum(r.get("origin") != "v1_reverified" for r in rows) == 20
assert all(r["evidence_status"] == "Evidence-Verified" for r in rows)
assert all(r["review_status"] == "Candidate" for r in rows)
assert all(r["expert_review_status"] != "Expert-Approved" for r in rows)
for r in rows:
    assert r["source_ids"] and r["evidence_locations"] and r["key_answer_points"]
    assert not any(x in r["question"] for x in ("根据教材", "教材指出", "如图所示", "根据上述", "根据某篇论文", "作者认为"))
for r in rows:
    if r["question_type"] == "K4":
        assert len(r["required_concepts"]) >= 2
    if r["question_type"] == "K5":
        assert r["applicability"]
print("PASS: 33 candidates; 13 reverified + 20 new; traceability, wording, K4/K5 checks passed")
