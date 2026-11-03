import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def rows(p): return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
claims=rows(R/'datasets/claim_evidence_audit.jsonl'); patches=rows(R/'datasets/candidate_patches.jsonl'); holds=rows(R/'datasets/items_on_hold.jsonl')
assert len(claims)==9 and len(patches)==8 and len(holds)==5
assert all({'claim_id','factual_status','evidence_support','applicability_status'}<=x.keys() for x in claims)
assert all(x['expert_adjudication_required'] for x in patches)
print({'result':'PASS','claims':len(claims),'patches':len(patches),'holds':len(holds),'expert_results':0})
