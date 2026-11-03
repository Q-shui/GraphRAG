"""Deterministic reference tools for the P1 retrospective QA prototype.

This module makes no engineering interpretation of the two numeric fields.
It is an auditable CSV calculator, not an agent.
"""
from __future__ import annotations
import csv, math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'qa_smoke_test' / 'daily_reports_raw_extract.csv'
FIELDS = {'average_voltage', 'working_voltage'}
VERSION = 'p1-daily-extract-v1'

class QAError(ValueError):
    def __init__(self, code, message): super().__init__(message); self.code = code

def _date(value):
    try: return date.fromisoformat(str(value)[:10].replace('/', '-'))
    except ValueError as exc: raise QAError('E_INVALID_DATE', 'date must be YYYY-MM-DD') from exc

def _number(value): return None if value in (None, '', 'None') else float(value)

def load(path=INPUT):
    rows=[]
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        for raw in csv.DictReader(handle):
            try:
                rows.append({'source_file':raw['source_file'], 'source_row':int(raw['source_row']),
                    'cell_id':int(float(raw['cell_id'])), 'record_date':_date(raw['record_date']),
                    'average_voltage':_number(raw['average_voltage']), 'working_voltage':_number(raw['working_voltage'])})
            except (KeyError, TypeError, ValueError, QAError) as exc:
                raise QAError('E_INVALID_SOURCE_ROW', f'invalid source-derived row: {raw!r}') from exc
    return rows

def _validate(cell_id, start_date, end_date, field):
    if type(cell_id) is not int: raise QAError('E_INVALID_TYPE', 'cell_id must be an integer')
    if field not in FIELDS: raise QAError('E_UNSUPPORTED_FIELD', f'field must be one of {sorted(FIELDS)}')
    start,end=_date(start_date),_date(end_date)
    if start>end: raise QAError('E_INVALID_BOUNDS', 'start_date must not be after end_date')
    return start,end

def _key(row): return (row['cell_id'],row['record_date'],row['average_voltage'],row['working_voltage'])

def deduplicate_exact(rows):
    ordered=sorted(rows,key=lambda x:(x['source_file'],x['source_row'])); out=[]; seen=set()
    for row in ordered:
        if _key(row) not in seen: seen.add(_key(row));out.append(row)
    return out,len(ordered)-len(out)

def _records(rows, cell_id, start, end, duplicate_policy='deduplicated_exact'):
    chosen=[r for r in rows if r['cell_id']==cell_id and start<=r['record_date']<=end]
    if not chosen: raise QAError('E_NO_RECORDS','no records for cell and inclusive date bounds')
    if duplicate_policy=='raw': return chosen,0
    if duplicate_policy!='deduplicated_exact': raise QAError('E_INVALID_DUPLICATE_POLICY','duplicate_policy must be raw or deduplicated_exact')
    clean,removed=deduplicate_exact(chosen); by_day=defaultdict(set)
    for r in clean: by_day[r['record_date']].add((r['average_voltage'],r['working_voltage']))
    conflicts=[d.isoformat() for d,v in by_day.items() if len(v)>1]
    if conflicts: raise QAError('E_CONFLICTING_RECORDS','conflicting same-cell/day records: '+','.join(conflicts))
    return clean,removed

def get_record(rows,cell_id,record_date,field):
    day,_=_validate(cell_id,record_date,record_date,field); records,removed=_records(rows,cell_id,day,day); record=records[0]
    return {'dataset_version':VERSION,'cell_id':cell_id,'date':day.isoformat(),'field':field,'value':record[field],
      'source_file':record['source_file'],'source_row':record['source_row'],'duplicates_removed':removed,'unit':'unknown'}

def calculate_statistics(rows,cell_id,start_date,end_date,field):
    start,end=_validate(cell_id,start_date,end_date,field);records,removed=_records(rows,cell_id,start,end)
    values=[r[field] for r in records if r[field] is not None]
    if not values: raise QAError('E_NO_VALID_VALUES','records exist but selected field is null')
    mean=sum(values)/len(values);observed=len({r['record_date'] for r in records})
    return {'dataset_version':VERSION,'cell_id':cell_id,'field':field,'start_date':start.isoformat(),'end_date':end.isoformat(),
      'raw_record_count':len(records)+removed,'record_count_after_deduplication':len(records),'valid_record_count':len(values),
      'missing_record_count':len(records)-len(values),'mean':mean,'min':min(values),'max':max(values),
      'population_sd':math.sqrt(sum((x-mean)**2 for x in values)/len(values)),'calendar_days':(end-start).days+1,'observed_days':observed,
      'gap_warning':observed<(end-start).days+1,'duplicates_removed':removed,'unit':'unknown','date_rule':'inclusive','null_rule':'excluded from numeric statistic'}

def compare_time_windows(rows,cell_id,field,first,second):
    a=calculate_statistics(rows,cell_id,first[0],first[1],field);b=calculate_statistics(rows,cell_id,second[0],second[1],field)
    return {'dataset_version':VERSION,'cell_id':cell_id,'field':field,'first_window':a,'second_window':b,'mean_difference_second_minus_first':b['mean']-a['mean'],'unit':'unknown'}

def compare_cells(rows,cell_a,cell_b,start_date,end_date,field):
    a=calculate_statistics(rows,cell_a,start_date,end_date,field);b=calculate_statistics(rows,cell_b,start_date,end_date,field)
    return {'dataset_version':VERSION,'field':field,'cell_a':a,'cell_b':b,'mean_difference_b_minus_a':b['mean']-a['mean'],'unit':'unknown','interpretation_limit':'descriptive comparison only; no production-performance inference'}

def inspect_data_quality(rows,cell_id=None,start_date=None,end_date=None):
    selected=rows
    if cell_id is not None:
        if type(cell_id) is not int: raise QAError('E_INVALID_TYPE','cell_id must be an integer')
        selected=[r for r in selected if r['cell_id']==cell_id]
    if start_date is not None or end_date is not None:
        if start_date is None or end_date is None: raise QAError('E_INVALID_BOUNDS','both date bounds are required')
        start,end=_date(start_date),_date(end_date)
        if start>end: raise QAError('E_INVALID_BOUNDS','start_date must not be after end_date')
        selected=[r for r in selected if start<=r['record_date']<=end]
    counts=Counter(_key(r) for r in selected)
    return {'dataset_version':VERSION,'raw_record_count':len(selected),'exact_duplicate_rows':sum(n-1 for n in counts.values() if n>1),
      'missing_average_voltage':sum(r['average_voltage'] is None for r in selected),'missing_working_voltage':sum(r['working_voltage'] is None for r in selected),
      'cell_ids':sorted({r['cell_id'] for r in selected}),'unit':'unknown'}
