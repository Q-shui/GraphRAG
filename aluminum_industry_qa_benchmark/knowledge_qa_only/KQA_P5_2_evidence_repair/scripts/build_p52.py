import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; K=R.parent; D=R/'datasets'; D.mkdir(parents=True,exist_ok=True)
def read(p): return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def write(name, xs): (D/name).write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in xs)+'\n',encoding='utf8')
p4=read(K/'KQA_P4_dataset_construction/datasets/questions.jsonl'); p5=read(K/'KQA_P5_web_engineering_knowledge/datasets/new_qa_candidates.jsonl'); p51=read(K/'KQA_P5_1_evidence_expansion/datasets/new_qa_candidates.jsonl')
focus={'W502','W504','W505','W506','W510','X511','X514','X515'}
claims=[]
data={
'W502':[('C-W502-1','阳极效应期间不产铝不等于所有过程投入停止','EPA-AL-2026','P5 source record; full direct independent evidence not located','single-source/needs direct verification','uncertain','facility and AE-type dependent','none located','HOLD','REVISE')],
'W504':[('C-W504-1','过快下料或大增量可来不及溶解并形成槽底沉积','DOE-ITP-2003','P5 source record','direct but single engineering source','provisional','depends on feed, dissolution, bath and flow conditions','SFU alumina paper inaccessible; CFD article 403','none assessed','REVISE')],
'W505':[('C-W505-1','下料控制须考虑局部浓度均匀性及异常风险','IFAC-2018-SPF','abstract-only record','abstract only','uncertain','industrial control objective, not universal causal proof','SFU paper inaccessible','none assessed','HOLD')],
'W506':[('C-W506-1','局部低压阳极效应可在很小阳极区域发生','SINTEF-2022-LVAE','abstract-only P5 record','abstract only','uncertain','model-specific unless independently observed','SINTEF-2015-PAE laboratory abstract supports differing anode current uptake, not full model','no direct conflict','REVISE'),('C-W506-2','PFC可在未显著升压的工况产生','IPCC-2019-METAL','IPCC Ch4 Box 4.2','direct','verified','inventory/HVAE-LVAE definition; not local spatial mechanism','SINTEF-2015-PAE laboratory abstract','none assessed','RETAIN')],
'W510':[('C-W510-1','BAT资料不可直接作为普适电化学因果结论','JRC-NFM-2016','P5 source record','direct for regulatory scope; causal extrapolation is methodological inference','provisional','specific regulatory and technology context','none assessed','none assessed','REVISE')],
'X511':[('C-X511-1','AE分钟数需由频率与平均持续时间构成','EURLex-PFC','EU page blocked by JS verification','not full-text verified this round','uncertain','specified EU calculation method only','IPCC records AE minutes differently as total recorded minutes per cell-day','method-definition mismatch; not a factual conflict','HOLD')],
'X514':[('C-X514-1','未访问某论文全文时不能给出具体集流棒寿命/机理','MAT-2026-CB','landing page 403','valid only as current evidence-access limitation','not a permanent aluminium fact','temporary access condition','SINTEF-2017 cathode autopsy provides a different cathode-wear source','not applicable','MOVE_TO_EVIDENCE_TASK')],
'X515':[('C-X515-1','跨槽能耗比较需说明侧壁散热和槽型尺度','JSTAGE-2005-ENERGY','abstract-only P5.1 record','abstract only','uncertain','qualitative thermal-boundary claim','none located','none assessed','HOLD')]
}
for q,cs in data.items():
 for c in cs:
  claims.append(dict(zip(['claim_id','question_id','claim_text','source_id','source_location','evidence_support','factual_status','applicability_status','independent_support','conflicting_evidence','recommendation'],c)) | {'access_level': ('full text' if c[3].startswith('IPCC') else 'abstract/source-record/blocked as stated'),'review_notes':'See report 03; factual status, evidence support and applicability are intentionally separate.'})
write('claim_evidence_audit.jsonl',claims)
patches=[]
for q in focus:
 orig=next(x for x in p5+p51 if x['question_id']==q)
 rec={'W502':'HOLD','W504':'REVISE','W505':'HOLD','W506':'REVISE','W510':'REVISE','X511':'HOLD','X514':'MOVE_TO_EVIDENCE_TASK','X515':'HOLD'}[q]
 newq={'W502':'在已限定的高压阳极效应语境下，如何区分“无正常产铝”与“槽整体所有能量、物料过程均停止”？','W504':'在何种下料、料性、浴况和流动条件下，快速或大批量氧化铝加入可能增加未充分溶解/沉积风险？','W505':'在给定槽型、加料位置和浓度测量条件下，如何评价下料分布与局部浓度均匀性？','W506':'低压阳极效应排放可不越过电压阈值这一核算事实，能否推出其必然局部化？','W510':'在特定 BAT 文件适用范围内，哪些是环境管理建议，哪些不能直接视为普适电化学因果？','X511':orig['question'],'X514':'给定某一材料论文仅有书目信息、尚未访问正文时，能否据此给出具体集流棒服役温度、寿命或失效机理？','X515':orig['question']}[q]
 ans={'W502':'不能。应分别说明所讨论阳极效应类型、正常阴极产铝反应、总电流/能量输入和物料过程；现有资料不足以作所有阳极效应状态的绝对断言。','W504':'应回答条件化风险而非单因果：下料速率/批量与料性、浴温/过热度、流场和既有沉积状态共同决定溶解与沉积结果。','W505':'需要给出槽型、加料位置、浓度观测与运行状态；没有这些条件，不能从一个控制案例推出通用最优策略。','W506':'不能。IPCC 支持电压阈值并非 PFC 排放的充分判据；局部化仍须由独立空间分辨实验或受验证模型支持。','W510':'BAT 可支持其文件规定的环境管理讨论；若要提出电化学因果，须另有机理或实验来源。','X511':'HOLD：本轮无法访问指定 EU 原文，且不同核算方法对 AE 分钟数据的定义应逐方法核验。','X514':'不能。该结论是给定证据条件下的信息充分性判断，应放入证据评测/审计队列，而非普通专业知识金标准。','X515':'HOLD：只保留“能耗比较须说明热边界”的定性限制；全文和具体槽型范围未核验。'}[q]
 patches.append({'patch_id':'P52-'+q,'question_id':q,'original_question':orig['question'],'original_reference_answer':orig['reference_answer'],'evidence_defect':'see claim_evidence_audit','proposed_question':newq,'proposed_reference_answer':ans,'pre_conditions':orig.get('applicable_conditions',''),'post_conditions':'explicitly stated in proposed answer','rubric_impact':'require conditions and scope; no unsupported universal causal statement','reverification_required':rec in {'REVISE','HOLD'},'expert_adjudication_required':True,'recommendation':rec})
write('candidate_patches.jsonl',patches)
hold=[{'question_id':x['question_id'],'reason':x['recommendation'],'queue':'evidence/experts','release_action':'exclude from internal benchmark view until resolved'} for x in patches if x['recommendation'] in {'HOLD','MOVE_TO_EVIDENCE_TASK'}]
write('items_on_hold.jsonl',hold)
# 75-item reviewer input; statuses are risk triage, not review decisions
allq=p4+p5+p51
rows=[]
for x in allq:
 t=x.get('primary_type',''); high=x['question_id'] in focus or t in {'K4','K5','K6','E1'}
 rows.append({'question_id':x['question_id'],'priority':'P1' if high else ('P2' if t in {'K2','K3'} else 'P3'),'knowledge_domain':x.get('knowledge_domain',''),'question':x['question'],'reference_answer':x.get('reference_answer','see linked answer dataset'),'key_answer_points':' | '.join(x.get('key_answer_points',[])),'evidence_location':'see source/evidence mapping; P52 focus items in claim_evidence_audit','applicability':x.get('applicable_conditions',''),'review_status':'Not-Reviewed'})
(R/'review').mkdir(exist_ok=True); (R/'review/reviewer_rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print({'items':len(rows),'claims':len(claims),'patches':len(patches),'hold':len(hold)})
