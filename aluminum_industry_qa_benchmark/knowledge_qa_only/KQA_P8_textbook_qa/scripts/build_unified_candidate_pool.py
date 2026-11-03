import json, hashlib, re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
B=R.parent
inputs=[
 ('P4',B/'KQA_P4_dataset_construction/datasets/questions.jsonl',B/'KQA_P4_dataset_construction/datasets/answers.jsonl'),
 ('P5',B/'KQA_P5_web_engineering_knowledge/datasets/new_qa_candidates.jsonl',None),
 ('P5.1',B/'KQA_P5_1_evidence_expansion/datasets/new_qa_candidates.jsonl',None),
 ('P6',B/'KQA_P6_benchmark_scaling/datasets/questions.jsonl',B/'KQA_P6_benchmark_scaling/datasets/answers.jsonl'),
 ('P7-001',B/'KQA_P7_scaling/datasets/questions.jsonl',B/'KQA_P7_scaling/datasets/answers.jsonl'),
 ('P7-002',B/'KQA_P7_scaling/datasets/batch002_questions.jsonl',B/'KQA_P7_scaling/datasets/batch002_answers.jsonl'),
 ('P7-003',B/'KQA_P7_scaling/datasets/batch003_questions.jsonl',B/'KQA_P7_scaling/datasets/batch003_answers.jsonl'),
 ('P8-001',R/'datasets/textbook_questions.jsonl',None)]
def norm(s): return re.sub(r'\W','',s).lower()
out=[]; seen={}; exact=[]
for project,p,ap in inputs:
 answers={}
 if ap:
  answers={x['question_id']:x for x in (json.loads(line) for line in ap.read_text(encoding='utf8').splitlines() if line.strip())}
 for line in p.read_text(encoding='utf8').splitlines():
  if not line.strip(): continue
  x=json.loads(line); q=x.get('question','')
  key=norm(q)
  if key in seen:
   exact.append({'discarded_project':project,'discarded_id':x.get('question_id'),'kept_id':seen[key],'reason':'exact normalized question duplicate'})
   continue
  seen[key]=x.get('question_id')
  a=answers.get(x.get('question_id'),{})
  out.append({'pool_id':f'{project}:{x.get("question_id")}', 'source_project':project, 'source_question_id':x.get('question_id'), 'question':q, 'reference_answer':x.get('reference_answer') or a.get('reference_answer'), 'key_answer_points':x.get('key_answer_points') or a.get('key_answer_points'), 'primary_type':x.get('primary_type'), 'knowledge_domain':x.get('knowledge_domain'), 'difficulty':x.get('difficulty'), 'source_ids':x.get('source_ids'), 'evidence_locations':x.get('evidence_locations',x.get('source_locations')), 'evidence_status':x.get('evidence_status',x.get('evidence_review_status','HISTORICAL_STATUS_UNMAPPED')), 'expert_review_status':x.get('expert_review_status','Not-Reviewed'), 'candidate_status':x.get('candidate_status','Candidate'), 'family_id':x.get('question_family_id'), 'eligibility':'Candidate pool only; no train/dev/test assignment.'})
D=R/'datasets'; D.mkdir(exist_ok=True)
(D/'unified_candidate_pool.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in out)+'\n',encoding='utf8')
(D/'unified_exact_duplicates.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in exact)+'\n',encoding='utf8')
raw=(D/'unified_candidate_pool.jsonl').read_bytes()
manifest={'input_files':[str(p) for _,p,_ in inputs],'answer_files':[str(a) for _,_,a in inputs if a],'candidate_count':len(out),'exact_duplicates_removed':len(exact),'sha256':hashlib.sha256(raw).hexdigest().upper(),'limitation':'Exact-text de-duplication only. Semantic-family audit and expert review are still required before a formal benchmark split.'}
(R/'manifests'/'UNIFIED_CANDIDATE_POOL_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
