"""Independent arithmetic verifier: deliberately does not import calculator internals."""
import csv,json,math
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'qa_smoke_test'/'daily_reports_raw_extract.csv'; PROTO=ROOT/'dataset_prototype'/'p1_qa_prototype.jsonl'
def rows():
 with DATA.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def stat(rs,cell,start,end,field):
 s=date.fromisoformat(start);e=date.fromisoformat(end); seen=set();vals=[];alln=0
 for r in sorted(rs,key=lambda x:(x['source_file'],int(x['source_row']))):
  d=date.fromisoformat(r['record_date'][:10].replace('/','-')); key=(r['cell_id'],d,r['average_voltage'],r['working_voltage'])
  if key in seen:continue
  seen.add(key)
  if int(float(r['cell_id']))==cell and s<=d<=e:
   alln+=1
   if r[field]!='':vals.append(float(r[field]))
 if not vals:raise AssertionError('no values')
 mean=sum(vals)/len(vals);return {'mean':mean,'population_sd':math.sqrt(sum((x-mean)**2 for x in vals)/len(vals)),'valid_record_count':len(vals),'record_count_after_deduplication':alln}
def close(a,b):return abs(a-b)<=1e-6
def main():
 rs=rows(); checks=[]
 for x in map(json.loads,PROTO.read_text(encoding='utf-8').splitlines()):
  if x['task_type']=='T1_record_query':
   ref=x['reference_answer']; found=[r for r in rs if int(float(r['cell_id']))==2726 and r['record_date'][:10].replace('/','-')=='2017-06-23'][0]
   checks.append([x['question_id'],close(float(found['average_voltage']),ref['value']) and int(found['source_row'])==ref['source_row']])
  elif x['task_type']=='T2_statistics':
   got=stat(rs,x['cell_id'],x['start_date'],x['end_date'],x['field']);ref=x['reference_answer'];ok=all(got[k]==ref[k] if isinstance(got[k],int) else close(got[k],ref[k]) for k in got);checks.append([x['question_id'],ok])
  elif x['task_type']=='T3_time_window_compare':
   ref=x['reference_answer']; a=stat(rs,2726,'2017-06-23','2017-06-30','average_voltage');b=stat(rs,2726,'2017-07-01','2017-07-08','average_voltage')
   checks.append([x['question_id'],close(b['mean']-a['mean'],ref['mean_difference_second_minus_first'])])
  elif x['task_type']=='T4_cross_cell_compare':
   ref=x['reference_answer']; a=stat(rs,2726,'2017-06-23','2017-06-30','average_voltage');b=stat(rs,2730,'2017-06-23','2017-06-30','average_voltage')
   checks.append([x['question_id'],close(b['mean']-a['mean'],ref['mean_difference_b_minus_a'])])
  elif x['question_id']=='P1Q006':
   keys=[(r['cell_id'],r['record_date'],r['average_voltage'],r['working_voltage']) for r in rs]; dup=len(keys)-len(set(keys));ref=x['reference_answer']
   checks.append([x['question_id'],len(rs)==ref['raw_record_count'] and dup==ref['exact_duplicate_rows'] and sum(r['working_voltage']=='' for r in rs)==ref['missing_working_voltage']])
  elif x['question_id']=='P1Q007':
   got=stat(rs,2726,'2017-06-23','2017-06-30','average_voltage');ref=x['reference_answer']; checks.append([x['question_id'],got['valid_record_count']==8 and ref['calendar_days']==8 and ref['observed_days']==8 and ref['gap_warning'] is False])
 # canonical regression independent from calculator
 got=stat(rs,2726,'2017-06-23','2017-06-30','average_voltage');checks.append(['regression_2726_mean',close(got['mean'],4.249375)])
 if not all(x[1] for x in checks):raise SystemExit(json.dumps(checks,ensure_ascii=False))
 print(json.dumps({'status':'PASS','checks':checks},ensure_ascii=False))
if __name__=='__main__':main()
