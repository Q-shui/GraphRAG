import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]
e=[json.loads(x) for x in (r/'datasets/evidence_qa_candidates.jsonl').read_text(encoding='utf8').splitlines() if x]
m=[json.loads(x) for x in (r/'datasets/management_qa_candidates.jsonl').read_text(encoding='utf8').splitlines() if x]
assert len(e)==6 and len(m)==2
assert {x['assessment_mode'] for x in e}=={'A','B'}
assert all(x['review_status']=='Candidate' and x['expert_review_status']=='Not-Reviewed' for x in e+m)
assert all(x['evidence_ids'] and x['source_locations'] for x in e+m)
assert all('根据教材' not in x['question'] for x in e+m)
print('PASS: 6 E1 and 2 management candidates; modes, traceability, frozen-status rules verified')
