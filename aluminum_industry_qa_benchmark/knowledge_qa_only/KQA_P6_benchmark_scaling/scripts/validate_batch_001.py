import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'datasets'
def rows(n):return [json.loads(x) for x in (D/n).read_text(encoding='utf8').splitlines() if x.strip()]
q,a,r,s,k,e,b=map(rows,['questions.jsonl','answers.jsonl','rubrics.jsonl','sources.jsonl','knowledge_units.jsonl','evidence.jsonl','benchmark_view.jsonl'])
ids={x['question_id'] for x in q};assert len(q)==15==len(ids);assert {x['question_id'] for x in a}==ids=={x['question_id'] for x in r};assert all(x['source_id'] in {z['source_id'] for z in s} for x in e);assert len(b)==10;assert all('根据' not in x['question'] and '文献' not in x['question'] for x in q)
out={'result':'PASS','questions':len(q),'review_ready':len(b),'restricted_candidates':5,'sources':len(s),'knowledge_units':len(k),'sha256_questions':hashlib.sha256((D/'questions.jsonl').read_bytes()).hexdigest().upper()};(R/'validation/batch_001_result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(out)
