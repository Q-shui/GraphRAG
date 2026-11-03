"""P2-B2 deterministic reference-tool façade over the frozen P1 CSV snapshot."""
from __future__ import annotations
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
P1S=Path(__file__).resolve().parents[3]/'P1_semantic_calibration'/'scripts'
sys.path.insert(0,str(P1S)); import qa_reference_calculator as calc

TOOL_SCHEMA_VERSION='p2-data-tools-v1'
ALLOWED_FIELDS=sorted(calc.FIELDS)
def _iso(v): return v.isoformat() if isinstance(v,date) else v
def _serial(row): return {k:_iso(v) for k,v in row.items()}
def _ensure_bounds(start,end):
 s,e=calc._date(start),calc._date(end)
 if s>e: raise calc.QAError('E_INVALID_BOUNDS','start_date must not be after end_date')
 return s,e
def get_schema():
 return {'tool_schema_version':TOOL_SCHEMA_VERSION,'dataset_version':calc.VERSION,'fields':ALLOWED_FIELDS,'date_bounds':'inclusive','duplicate_policy':'deduplicated_exact for statistics; raw provenance retained for queries','units':'unknown','errors':['E_INVALID_DATE','E_INVALID_TYPE','E_UNSUPPORTED_FIELD','E_INVALID_BOUNDS','E_NO_RECORDS','E_NO_VALID_VALUES','E_CONFLICTING_RECORDS']}
def query_records(cell_id,start_date,end_date,fields=None):
 if type(cell_id) is not int: raise calc.QAError('E_INVALID_TYPE','cell_id must be an integer')
 start,end=_ensure_bounds(start_date,end_date); fields=fields or ALLOWED_FIELDS
 if not set(fields)<=set(ALLOWED_FIELDS): raise calc.QAError('E_UNSUPPORTED_FIELD','requested field is not allowed')
 rows=[r for r in calc.load() if r['cell_id']==cell_id and start<=r['record_date']<=end]
 if not rows: raise calc.QAError('E_NO_RECORDS','no records for cell and inclusive date bounds')
 return {'dataset_version':calc.VERSION,'date_rule':'inclusive','cell_id':cell_id,'fields':fields,'records':[{k:_serial(r)[k] for k in ['source_file','source_row','cell_id','record_date',*fields]} for r in rows]}
def filter_records(records,field,not_null=True):
 if field not in calc.FIELDS: raise calc.QAError('E_UNSUPPORTED_FIELD','field is not allowed')
 out=[r for r in records if (r.get(field) is not None)==not_null]
 return {'field':field,'not_null':not_null,'record_count':len(out),'records':out}
def calculate_statistics(cell_id,start_date,end_date,field): return calc.calculate_statistics(calc.load(),cell_id,start_date,end_date,field)
def compare_time_windows(cell_id,field,first,second): return calc.compare_time_windows(calc.load(),cell_id,field,tuple(first),tuple(second))
def compare_cells(cell_a,cell_b,start_date,end_date,field): return calc.compare_cells(calc.load(),cell_a,cell_b,start_date,end_date,field)
def inspect_data_quality(cell_id=None,start_date=None,end_date=None):
 rows=calc.load(); selected=rows
 if cell_id is not None:
  if type(cell_id) is not int: raise calc.QAError('E_INVALID_TYPE','cell_id must be an integer')
  selected=[r for r in selected if r['cell_id']==cell_id]
 if start_date is not None or end_date is not None:
  if start_date is None or end_date is None: raise calc.QAError('E_INVALID_BOUNDS','both date bounds are required')
  s,e=_ensure_bounds(start_date,end_date); selected=[r for r in selected if s<=r['record_date']<=e]
 unique,removed=calc.deduplicate_exact(selected); groups=defaultdict(set)
 for r in unique: groups[(r['cell_id'],r['record_date'])].add((r['average_voltage'],r['working_voltage']))
 conflicts=sorted([{'cell_id':c,'record_date':d.isoformat()} for (c,d),x in groups.items() if len(x)>1],key=lambda x:(x['cell_id'],x['record_date']))
 coverage=None
 if cell_id is not None and start_date is not None:
  s,e=_ensure_bounds(start_date,end_date); dates={r['record_date'] for r in unique}; missing=[(s.fromordinal(n)).isoformat() for n in range(s.toordinal(),e.toordinal()+1) if s.fromordinal(n) not in dates]
  coverage={'calendar_days':(e-s).days+1,'observed_days':len(dates),'missing_dates':missing,'gap_warning':bool(missing)}
 return {'dataset_version':calc.VERSION,'raw_record_count':len(selected),'exact_duplicate_rows_on_extract_fields':removed,'conflicting_same_cell_day_count':len(conflicts),'conflicts':conflicts,'coverage':coverage,'scope':{'cell_id':cell_id,'start_date':start_date,'end_date':end_date},'unit':'unknown'}
def refuse_unsupported_inference(requested_conclusion,field):
 if field not in calc.FIELDS: raise calc.QAError('E_UNSUPPORTED_FIELD','field is not allowed')
 return {'dataset_version':calc.VERSION,'status':'INSUFFICIENT_EVIDENCE','requested_conclusion':requested_conclusion,'field':field,'reason':'The frozen snapshot supports retrospective record/statistical results only; field unit, aggregation, availability and business mapping are not directly confirmed.','required_direct_evidence':['data dictionary','unit and aggregation definition','availability/revision rule','recorded business-event or control mapping']}

TOOLS={'get_schema':get_schema,'query_records':query_records,'filter_records':filter_records,'calculate_statistics':calculate_statistics,'compare_time_windows':compare_time_windows,'compare_cells':compare_cells,'inspect_data_quality':inspect_data_quality,'refuse_unsupported_inference':refuse_unsupported_inference}
def execute_sequence(calls):
 outputs=[]
 for call in calls:
  try: outputs.append({'tool':call['tool'],'output':TOOLS[call['tool']](**call.get('arguments',{}))})
  except calc.QAError as e: outputs.append({'tool':call['tool'],'error':{'code':e.code,'message':str(e)}})
 return outputs
