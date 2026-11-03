import sys
import json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reference_tools'))
import p2_data_tools as t
def code(fn):
 try:fn()
 except Exception as e:return getattr(e,'code',None)
 return None
def main():
 s=t.get_schema();assert s['dataset_version']=='p1-daily-extract-v1' and set(s['fields'])=={'average_voltage','working_voltage'}
 assert len(t.query_records(2726,'2017-06-23','2017-06-25',['average_voltage'])['records'])==3
 assert t.calculate_statistics(2726,'2017-06-23','2017-06-30','average_voltage')['mean']==4.249375
 assert t.inspect_data_quality()['exact_duplicate_rows_on_extract_fields']==63
 assert code(lambda:t.query_records('2726','2017-06-23','2017-06-25'))=='E_INVALID_TYPE'
 assert code(lambda:t.query_records(2726,'2017-06-25','2017-06-23'))=='E_INVALID_BOUNDS'
 assert code(lambda:t.calculate_statistics(2726,'2017-06-23','2017-06-30','noise'))=='E_UNSUPPORTED_FIELD'
 assert code(lambda:t.query_records(9999,'2017-06-23','2017-06-25'))=='E_NO_RECORDS'
 tasks=[json.loads(x) for x in (Path(__file__).resolve().parents[1]/'datasets'/'data_qa_candidates.jsonl').read_text(encoding='utf-8').splitlines()]
 assert len(tasks)==11 and len({x['question_id'] for x in tasks})==11
 for task in tasks:
  outputs=t.execute_sequence(task['reference_tool_calls'])
  if task['question_id'] in {'D016','D017'}: assert outputs[-1]['error']['code'] in {'E_UNSUPPORTED_FIELD','E_NO_RECORDS'}
  else: assert all('output' in x for x in outputs)
 assert sum(x['computation_verification_status']=='Computation-Verified' for x in tasks)==10
 assert tasks[-1]['computation_verification_status']=='Not-applicable'
 print('PASS: schema, query, regression, quality, type/bounds/field/no-record errors')
if __name__=='__main__':main()
