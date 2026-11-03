"""Independent P2-B2 verifier: reads CSV directly and does not import reference tools/calculator."""
import csv,json,math
from collections import Counter,defaultdict
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT.parents[1]/'P1_semantic_calibration'/'qa_smoke_test'/'daily_reports_raw_extract.csv'; TASKS=ROOT/'datasets'/'data_qa_candidates.jsonl'
def load():
 out=[]
 with DATA.open(encoding='utf-8-sig',newline='') as f:
  for x in csv.DictReader(f): out.append({'source_file':x['source_file'],'source_row':int(x['source_row']),'cell_id':int(float(x['cell_id'])),'date':date.fromisoformat(x['record_date'][:10].replace('/','-')),'average_voltage':float(x['average_voltage']) if x['average_voltage'] else None,'working_voltage':float(x['working_voltage']) if x['working_voltage'] else None})
 return out
def dedup(rs):
 seen=set();out=[]
 for r in sorted(rs,key=lambda z:(z['source_file'],z['source_row'])):
  k=(r['cell_id'],r['date'],r['average_voltage'],r['working_voltage'])
  if k not in seen:seen.add(k);out.append(r)
 return out
def stat(rs,cell,start,end,field):
 s=date.fromisoformat(start);e=date.fromisoformat(end);x=[r for r in dedup(rs) if r['cell_id']==cell and s<=r['date']<=e];v=[r[field] for r in x if r[field] is not None]
 if not x:return None
 if not v:return 'NO_VALID'
 avg=sum(v)/len(v);return {'mean':avg,'min':min(v),'max':max(v),'population_sd':math.sqrt(sum((z-avg)**2 for z in v)/len(v)),'valid_record_count':len(v),'missing_record_count':len(x)-len(v),'record_count_after_deduplication':len(x)}
def close(a,b):return abs(a-b)<=1e-6
def main():
 rs=load(); tasks={x['question_id']:x for x in map(json.loads,TASKS.read_text(encoding='utf-8').splitlines())}; results=[]
 # D009 raw query
 a=tasks['D009']['reference_answer']; results.append(('D009',[(r['record_date'],r['average_voltage'],r['source_row']) for r in a['records']]==[('2017-06-23',4.915,2),('2017-06-24',4.412,3),('2017-06-25',4.227,4)]))
 for qid,cell,field,start,end in [('D010',2726,'working_voltage','2017-06-23','2017-06-30')]:
  got=stat(rs,cell,start,end,field);ref=tasks[qid]['reference_answer']; results.append((qid,all(got[k]==ref[k] if isinstance(got[k],int) else close(got[k],ref[k]) for k in got)))
 a=stat(rs,2726,'2017-06-23','2017-06-30','average_voltage');b=stat(rs,2726,'2017-07-01','2017-07-08','average_voltage');results.append(('D011',close(b['mean']-a['mean'],tasks['D011']['reference_answer']['mean_difference_second_minus_first'])))
 c=stat(rs,2730,'2017-06-23','2017-06-30','average_voltage');results.append(('D012',close(c['mean']-a['mean'],tasks['D012']['reference_answer']['mean_difference_b_minus_a'])))
 keys=[(r['cell_id'],r['date'],r['average_voltage'],r['working_voltage']) for r in rs]; byday=defaultdict(set)
 for r in dedup(rs):byday[(r['cell_id'],r['date'])].add((r['average_voltage'],r['working_voltage']))
 ref=tasks['D013']['reference_answer'];results.append(('D013',len(rs)==ref['raw_record_count'] and len(keys)-len(set(keys))==ref['exact_duplicate_rows_on_extract_fields'] and sum(r['working_voltage'] is None for r in rs)==162 and sum(len(v)>1 for v in byday.values())==ref['conflicting_same_cell_day_count']))
 sub=dedup([r for r in rs if r['cell_id']==2726 and date(2017,6,23)<=r['date']<=date(2021,6,2)]); observed={r['date'] for r in sub};missing=[date.fromordinal(x) for x in range(date(2017,6,23).toordinal(),date(2021,6,2).toordinal()+1) if date.fromordinal(x) not in observed];ref=tasks['D014']['reference_answer'];results.append(('D014',ref['coverage']['observed_days']==len(observed) and ref['coverage']['missing_dates']==[x.isoformat() for x in missing]))
 ref=tasks['D015']['reference_answer'];results.append(('D015',ref[1]['output']['mean']==a['mean'] and ref[2]['output']['coverage']['gap_warning'] is False))
 results += [('D016',tasks['D016']['reference_answer'][0]['error']['code']=='E_UNSUPPORTED_FIELD'),('D017',tasks['D017']['reference_answer'][0]['error']['code']=='E_NO_RECORDS'),('D018',tasks['D018']['reference_answer']['status']=='INSUFFICIENT_EVIDENCE')]
 if not all(ok for _,ok in results):raise SystemExit(json.dumps(results,ensure_ascii=False))
 print(json.dumps({'status':'PASS','checks':results},ensure_ascii=False))
if __name__=='__main__':main()
