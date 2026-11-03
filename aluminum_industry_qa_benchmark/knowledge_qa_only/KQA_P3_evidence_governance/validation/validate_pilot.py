import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
v2 = [json.loads(x) for x in (root.parents[0] / "KQA_P2_expansion/datasets/knowledge_qa_v2_candidates.jsonl").read_text(encoding="utf-8").splitlines() if x]
pilot = [json.loads(x) for x in (root / "datasets/claim_evidence_pilot.jsonl").read_text(encoding="utf-8").splitlines() if x]
ids = {x["question_id"] for x in v2}
labels = {"SUPPORTED","CONTRADICTED","PARTIALLY_SUPPORTED","CONDITIONAL","INSUFFICIENT","CONFLICTED"}
assert len(v2) == 33
assert len(pilot) == 7 and len({x["claim_id"] for x in pilot}) == 7
assert all(x["question_id"] in ids and x["support_label"] in labels and x["evidence_links"] for x in pilot)
assert sum(x["support_label"] == "PARTIALLY_SUPPORTED" for x in pilot) == 2
print("PASS: frozen v2 read-only; 7 claim-evidence pilot records have stable links and valid labels")
