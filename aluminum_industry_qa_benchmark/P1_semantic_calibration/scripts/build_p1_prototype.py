"""Build the immutable-looking P1 prototype JSONL and data-version manifest."""
from __future__ import annotations
import hashlib, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path
import qa_reference_calculator as q

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset_prototype'/'p1_qa_prototype.jsonl'
MANIFEST=ROOT/'manifests'/'p1_daily_extract_v1_manifest.json'
RAW_DIR=ROOT.parents[1]/'2020YFB1713603-001-电解铝跨工序能质耦合、工艺参数感知模型数据集'/'数据集实体文件'

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def task(qid,question,kind,cell,field,start,end,operation,call,answer,valid,warning='单位未确认；仅作回顾性描述'):
    return {'question_id':qid,'question':question,'task_type':kind,'source_dataset':'2020YFB1713603 daily XLS (derived read-only extract)',
      'dataset_version':q.VERSION,'cell_id':cell,'field':field,'start_date':start,'end_date':end,'filters':{'duplicate_policy':'deduplicated_exact','date_bounds':'inclusive'},
      'expected_operation':operation,'reference_tool_calls':call,'reference_answer':answer,'answer_unit':'unknown','answer_tolerance':1e-6,
      'valid_record_count':valid,'data_quality_warning':warning,'verification_status':'verified_independently'}

def main():
    rows=q.load(); OUT.parent.mkdir(exist_ok=True); MANIFEST.parent.mkdir(exist_ok=True)
    a=q.calculate_statistics(rows,2726,'2017-06-23','2017-06-30','average_voltage')
    work=q.calculate_statistics(rows,2726,'2017-06-23','2017-06-30','working_voltage')
    tw=q.compare_time_windows(rows,2726,'average_voltage',('2017-06-23','2017-06-30'),('2017-07-01','2017-07-08'))
    cc=q.compare_cells(rows,2726,2730,'2017-06-23','2017-06-30','average_voltage')
    rec=q.get_record(rows,2726,'2017-06-23','average_voltage')
    quality=q.inspect_data_quality(rows)
    records=[
      task('P1Q001','查询槽号2726在2017-06-23的平均电压原始记录值。','T1_record_query',2726,'average_voltage','2017-06-23','2017-06-23','get_record',
        [{'tool':'get_record','arguments':{'cell_id':2726,'record_date':'2017-06-23','field':'average_voltage'}}],rec,1),
      task('P1Q002','计算槽号2726在2017-06-23至2017-06-30（含端点）的平均电压均值和总体标准差。','T2_statistics',2726,'average_voltage','2017-06-23','2017-06-30','calculate_statistics',
        [{'tool':'calculate_statistics','arguments':{'cell_id':2726,'start_date':'2017-06-23','end_date':'2017-06-30','field':'average_voltage'}}],a,a['valid_record_count']),
      task('P1Q003','计算槽号2726在2017-06-23至2017-06-30（含端点）的工作电压均值和总体标准差。','T2_statistics',2726,'working_voltage','2017-06-23','2017-06-30','calculate_statistics',
        [{'tool':'calculate_statistics','arguments':{'cell_id':2726,'start_date':'2017-06-23','end_date':'2017-06-30','field':'working_voltage'}}],work,work['valid_record_count']),
      task('P1Q004','比较槽号2726在两个相邻8日窗口的平均电压均值：2017-06-23至06-30，与2017-07-01至07-08。','T3_time_window_compare',2726,'average_voltage','2017-06-23','2017-07-08','compare_time_windows',
        [{'tool':'compare_time_windows','arguments':{'cell_id':2726,'field':'average_voltage','first':['2017-06-23','2017-06-30'],'second':['2017-07-01','2017-07-08']}}],tw,16),
      task('P1Q005','比较槽号2726和2730在2017-06-23至2017-06-30（含端点）的平均电压描述统计；不得推断生产绩效。','T4_cross_cell_compare','2726_vs_2730','average_voltage','2017-06-23','2017-06-30','compare_cells',
        [{'tool':'compare_cells','arguments':{'cell_a':2726,'cell_b':2730,'start_date':'2017-06-23','end_date':'2017-06-30','field':'average_voltage'}}],cc,16,'单位未确认；只能描述数值差异，禁止性能/工艺优劣推断'),
      task('P1Q006','检查整个派生抽取中的完全重复行数和两个数值字段的缺失数。','T5_data_quality',None,None,None,None,'inspect_data_quality',
        [{'tool':'inspect_data_quality','arguments':{}}],quality,30691,'重复判断仅基于6列派生抽取；原始12字段完整重复审计见P0'),
      task('P1Q007','检查槽号2726在2017-06-23至2017-06-30的日期覆盖和缺口告警。','T5_data_quality',2726,'average_voltage','2017-06-23','2017-06-30','calculate_statistics',
        [{'tool':'calculate_statistics','arguments':{'cell_id':2726,'start_date':'2017-06-23','end_date':'2017-06-30','field':'average_voltage'}}],
        {'calendar_days':a['calendar_days'],'observed_days':a['observed_days'],'gap_warning':a['gap_warning'],'duplicates_removed':a['duplicates_removed']},a['valid_record_count'])]
    with OUT.open('w',encoding='utf-8',newline='\n') as f:
        for x in records:f.write(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
    raw=[]
    for p in sorted(RAW_DIR.glob('*.xls')): raw.append({'path':str(p),'sha256':sha256(p),'bytes':p.stat().st_size})
    scripts=[ROOT/'scripts'/'extract_daily_reports_readonly.ps1',ROOT/'scripts'/'qa_reference_calculator.py',Path(__file__)]
    manifest={'dataset_version':q.VERSION,'created_utc':datetime.now(timezone.utc).isoformat(),'raw_source_files':raw,
      'derived_extract':{'path':str(q.INPUT),'sha256':sha256(q.INPUT),'rows':len(rows),'columns':['source_file','source_row','cell_id','record_date','average_voltage','working_voltage']},
      'script_hashes':[{ 'path':str(p),'sha256':sha256(p)} for p in scripts], 'cell_ids':quality['cell_ids'],
      'duplicate_policy':{'raw_rows':len(rows),'exact_duplicate_rows_on_extract_fields':quality['exact_duplicate_rows'],'gold_default':'deduplicated_exact; retain earliest source_file/source_row; conflicting same-cell/day values are errors'},
      'date_parser':'first 10 characters; / normalized to -; ISO calendar date','field_names':sorted(q.FIELDS),'runtime':{'python':sys.version,'platform':platform.platform()}}
    MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'prototype_records':len(records),'manifest':str(MANIFEST),'prototype':str(OUT)},ensure_ascii=False))
if __name__=='__main__':main()
