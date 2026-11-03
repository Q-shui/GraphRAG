"""Create a separate P2 knowledge-only rewrite candidate set; original P2 file is never modified."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parents[0]/'P2_dual_track'/'P2_MVP'/'datasets'/'knowledge_qa_candidates.jsonl'
OUT=ROOT/'datasets'/'knowledge_qa_v1_candidates.jsonl'; AUDIT=ROOT/'review'/'old_15_question_audit.jsonl'
REWRITES={
'K001':'冷氧化铝加入电解质后，可能经历哪些主要去向？',
'K002':'氧化铝能否顺利溶解进入电解质，主要受哪些类别因素影响？',
'K004':'讨论大型预焙铝电解槽结构时，为什么不能把某一种槽型构型视为对所有工业铝电解槽都适用？',
'K005':'在冰晶石-氧化铝熔盐体系中采用炭阳极时，阳极效应通常指什么现象？',
'K006':'若仅观察到槽电压升高，能否对阳极效应作确定性诊断？还缺少哪些类型的信息？',
'K007':'在以槽电压 U(n)、系列电流 I(n) 和设定表观反电动势 B 表示的采样模型中，原始表观槽电阻 R0(n) 的关系式是什么？',
'K008':'在槽况解析中，为什么在给定采样模型下通常以表观槽电阻而非直接槽电压作为分析依据？',
'K009':'在表观槽电阻采样模型中，为什么 B 被设为常数会限制结果被解释为真实槽电阻的条件？',
'K010':'在早期单机群控的铝电解控制系统中，系统可采集或监控的两个主要信号类别是什么？',
'K011':'在大型预焙铝电解槽的常规生产中，哪些作业在所述技术条件下仍主要依赖人工或人工配合天车完成？',
'K012':'一点测定与多点测定在铝电解生产技术条件测量中分别适用于什么目的？',
'K015':'在传统定时下料控制模式中，效应等待开始后若发生停电或人工翻片，等待极限时间如何处理？',
}
DECISIONS={'K001':'REWRITE','K002':'REWRITE','K003':'RETAIN','K004':'REWRITE','K005':'REWRITE','K006':'REWRITE','K007':'REWRITE','K008':'REWRITE','K009':'REWRITE','K010':'REWRITE','K011':'REWRITE','K012':'REWRITE','K013':'REJECT','K014':'REJECT','K015':'REWRITE'}
REASONS={'K013':'依赖日报字段证据与统计窗口边界，不再属于纯知识 QA。','K014':'枚举式测量清单的专业区分度有限，且可与更高价值的条件题合并重构。','K006':'知识边界有效，但改写后须补充诊断所需信息的直接专业证据。','K015':'术语与控制系统版本限制显著，改写后必须重新核验。'}
def main():
 old=[json.loads(x) for x in OLD.read_text(encoding='utf-8').splitlines() if x]; updated=[]; audit=[]
 for x in old:
  qid=x['question_id']; decision=DECISIONS[qid]; newq=REWRITES.get(qid,x['question'])
  issue=[]
  if '教材' in x['question'] or '依据教材' in x['question']: issue.append('source-dependent wording')
  if qid=='K004':issue.append('implicit figure reference')
  if qid in {'K006','K013'}:issue.append('depends on former data-contract boundary')
  if qid=='K014':issue.append('enumeration-heavy low discrimination')
  audit.append({'question_id':qid,'original_question':x['question'],'decision':decision,'revised_question':newq if decision=='REWRITE' else None,'issues':issue,'reason':REASONS.get(qid,'remove source-dependent wording while retaining the supported knowledge claim'),'original_evidence_status':x['evidence_verification_status'],'rewrite_evidence_status':'Not-applicable' if decision=='REJECT' else ('Evidence-Verified' if decision=='RETAIN' else 'Needs-Reverification'),'expert_review_status':'Pending external domain-expert review'})
  if decision!='REJECT':
   y=dict(x); y['question']=newq; y['source_ids']=[x.pop('source_document_id')]; y['evidence_locations']=[x.pop('evidence_location')];y['knowledge_domain']=x.pop('knowledge_category'); y['required_concepts']=x.pop('required_knowledge_points');y['applicability']=x.pop('applicable_conditions');y['evidence_status']='Evidence-Verified' if decision=='RETAIN' else 'Needs-Reverification';y['review_status']='Candidate';y['source_group']=y['source_ids'][0];y['knowledge_unit_id']=qid;y['question_family_id']=qid;y['key_answer_points']=[y['reference_answer']];y['acceptable_alternatives']=[];y['reasoning_type']=y['question_type'];updated.append(y)
 OUT.parent.mkdir(parents=True,exist_ok=True);AUDIT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in updated),encoding='utf-8');AUDIT.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in audit),encoding='utf-8')
 print(json.dumps({'old':len(old),'new':len(updated),'decisions':{d:sum(a['decision']==d for a in audit) for d in ['RETAIN','REWRITE','MERGE','REJECT']}},ensure_ascii=False))
if __name__=='__main__':main()
