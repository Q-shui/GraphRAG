import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'datasets'/'knowledge_qa_candidates.jsonl'
REQ={'question_id','question','question_type','reference_answer','explanation','knowledge_category','process_stage','source_document_id','source_title','source_page','evidence_location','evidence_excerpt','applicable_conditions','required_knowledge_points','difficulty','uncertainty','evidence_verification_status','expert_review_status'}
def main():
 rows=[json.loads(x) for x in DATA.read_text(encoding='utf-8').splitlines() if x]
 assert len(rows)==15
 assert len({x['question_id'] for x in rows})==15
 assert all(set(x)==REQ for x in rows)
 assert all(x['evidence_verification_status']=='Evidence-Verified' for x in rows)
 assert all(x['expert_review_status']!='Expert-Approved' for x in rows)
 assert sum(x['question_type']=='K6' for x in rows)==2
 assert len({(x['source_document_id'],x['evidence_location']) for x in rows})>=8
 # Exact-question dedupe and answer leakage check, not a claim of semantic-model dedupe.
 assert len({x['question'] for x in rows})==15
 assert all(x['reference_answer'] not in x['question'] for x in rows)
 print('PASS: 15 records, schema, ids, evidence status, expert boundary, K6, source diversity, exact-duplicate/leakage screen')
if __name__=='__main__':main()
