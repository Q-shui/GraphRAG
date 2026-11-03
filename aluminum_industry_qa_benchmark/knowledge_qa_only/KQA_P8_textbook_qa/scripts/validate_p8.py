import json, hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=R/'datasets'; (R/'validation').mkdir(exist_ok=True); report=[]
required=['textbook_sources.jsonl','textbook_knowledge_units.jsonl','textbook_questions.jsonl','textbook_answers.jsonl','textbook_rubrics.jsonl','textbook_evidence.jsonl','textbook_audit_view.jsonl','textbook_benchmark_view.jsonl','pending_review.jsonl','rejected_candidates.jsonl']
for name in required:
 p=D/name; ok=p.exists(); rows=[]
 if ok:
  for line in p.read_text(encoding='utf8').splitlines():
   if line.strip(): rows.append(json.loads(line))
 report.append({'file':name,'exists':ok,'records':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper() if ok else None})
q=[json.loads(x) for x in (D/'textbook_questions.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
ids=[x['question_id'] for x in q]; assert len(ids)==len(set(ids)), 'question IDs not unique'
assert all('根据教材' not in x['question'] and '本章' not in x['question'] for x in q), 'textbook-dependent question'
rej=[json.loads(x) for x in (D/'rejected_candidates.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
assert all(x['candidate_status']=='REJECTED' and x.get('duplicate_of_question_id') for x in rej), 'rejected audit invalid'
pool=[json.loads(x) for x in (D/'unified_candidate_pool.jsonl').read_text(encoding='utf8').splitlines() if x.strip()]
assert len({x['pool_id'] for x in pool})==len(pool), 'unified pool IDs not unique'
assert len(pool)>=150, 'unified pool below the requested minimum quantity'
out={'status':'PASS','accepted_question_count':len(q),'unified_candidate_pool_count':len(pool),'rejected_duplicate_count':len(rej),'checks':['JSONL parse','required files','accepted ID uniqueness','no textbook-dependent accepted questions','rejection linkage','unified pool ID uniqueness','unified pool minimum quantity'],'files':report,'limitations':'PASS only verifies structure and quantity. It does not validate textbook pages, semantic near-duplicates, or domain correctness.'}
(R/'validation'/'validation_report.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(out,ensure_ascii=False,indent=2))
