import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]/'datasets'
def read(n): return [json.loads(x) for x in (R/n).read_text(encoding='utf8').splitlines() if x]
q,a,r,e,s=map(read,['questions.jsonl','answers.jsonl','rubrics.jsonl','evidence.jsonl','sources.jsonl'])
ids={x['question_id'] for x in q}
assert len(q)==len(ids)==59
assert {x['question_id'] for x in a}==ids=={x['question_id'] for x in r}
assert all(x['source_id'] in {z['source_id'] for z in s} or x['source_id'].startswith('EV-') for x in e)
bad=('根据教材','教材中提到','根据本章','如图所示','根据上述资料','按照本文的描述','某教材认为','作者指出','阅读以下段落后')
assert all(not any(b in x['question'] for b in bad) for x in q)
assert all(x['key_answer_points'] for x in a)
assert len({x['question'] for x in q})==59
print('PASS: 59 unique questions; IDs, sources, wording and rubrics verified')
