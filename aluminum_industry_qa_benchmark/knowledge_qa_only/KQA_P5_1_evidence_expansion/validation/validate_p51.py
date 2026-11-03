"""Deterministic structural and cross-version checks for the P5.1 working set."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KQA = ROOT.parent
FILES = {
    "p4": KQA / "KQA_P4_dataset_construction" / "datasets" / "questions.jsonl",
    "p5": KQA / "KQA_P5_web_engineering_knowledge" / "datasets" / "new_qa_candidates.jsonl",
    "p51": ROOT / "datasets" / "new_qa_candidates.jsonl",
}
REQUIRED = {"question_id", "question", "reference_answer", "source_ids", "rubric_id",
            "candidate_status", "evidence_review_status", "expert_review_status"}

def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main():
    p4, p5, p51 = (rows(FILES[k]) for k in ("p4", "p5", "p51"))
    p4_ids, p5_ids, p51_ids = ({x["question_id"] for x in xs} for xs in (p4, p5, p51))
    assert len(p4) == 59 and len(p5) == 10 and len(p51) == 6
    assert not (p4_ids & p5_ids or p4_ids & p51_ids or p5_ids & p51_ids)
    for item in p51:
        missing = REQUIRED - item.keys()
        assert not missing, (item["question_id"], missing)
        assert item["candidate_status"] == "Candidate"
        assert item["expert_review_status"] == "Not-Reviewed"
    questions = [x["question"].strip() for x in p4 + p5 + p51]
    assert len(questions) == len(set(questions)), "exact duplicate question"
    result = {
        "counts": {"P4": len(p4), "P5": len(p5), "P5.1": len(p51), "working_total": len(questions)},
        "sha256": {k: digest(v) for k, v in FILES.items()},
        "exact_question_duplicates": 0,
        "expert_approved_items": 0,
        "result": "PASS",
    }
    out = ROOT / "validation" / "validation_result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
