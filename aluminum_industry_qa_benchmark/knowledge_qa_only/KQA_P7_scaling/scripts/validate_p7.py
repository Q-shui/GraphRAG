import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'datasets'
def r(n):return [json.loads(x) for x in (D/n).read_text(encoding='utf8').splitlines() if x.strip()]
q,a,ru,s,e=map(r,['questions.jsonl','answers.jsonl','rubrics.jsonl','sources.jsonl','evidence.jsonl'])
ids={x['question_id'] for x in q};assert len(q)==25==len(ids);assert ids=={x['question_id'] for x in a}=={x['question_id'] for x in ru};assert all(x['source_id'] in {z['source_id'] for z in s} for x in e);assert all(x['evidence_tier'] in ['A','B'] for x in q);assert all(not any(t in x['question'] for t in ['根据教材','论文中提到','如图所示','按照上文']) for x in q)
o={'result':'PASS','new_candidates':25,'A':sum(x['evidence_tier']=='A' for x in q),'B':sum(x['evidence_tier']=='B' for x in q),'C':0,'sha256':hashlib.sha256((D/'questions.jsonl').read_bytes()).hexdigest().upper()};(R/'validation/result.json').write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf8');print(o)
