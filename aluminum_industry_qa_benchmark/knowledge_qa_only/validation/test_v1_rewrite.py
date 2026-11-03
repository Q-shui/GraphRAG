import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=[json.loads(x) for x in (root/'datasets'/'knowledge_qa_v1_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
audit=[json.loads(x) for x in (root/'review'/'old_15_question_audit.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(rows)==13 and len(audit)==15
assert sum(x['decision']=='RETAIN' for x in audit)==1 and sum(x['decision']=='REWRITE' for x in audit)==12 and sum(x['decision']=='REJECT' for x in audit)==2
assert all('教材' not in x['question'] and '根据' not in x['question'] and '如图' not in x['question'] for x in rows)
assert all(x['review_status']=='Candidate' for x in rows)
assert sum(x['evidence_status']=='Evidence-Verified' for x in rows)==1
print('PASS: independent wording screen, decisions, 13 non-rejected candidates, no inherited verification after rewrite')
