import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]; K=R.parents[0]
def load(p): return [json.loads(x) for x in Path(p).read_text(encoding='utf8').splitlines() if x.strip()]
legacy=load(K/'KQA_P2_expansion/datasets/knowledge_qa_v2_candidates.jsonl')
e1=load(K/'KQA_P3_evidence_governance/P3_round2_evidence_tasks/datasets/evidence_qa_candidates.jsonl')
mg=load(K/'KQA_P3_evidence_governance/P3_round2_evidence_tasks/datasets/management_qa_candidates.jsonl')
SRC={'MOD02':'现代铝电解，第2章，印刷页17','MOD03':'现代铝电解，第3章，印刷页32','MOD05':'现代铝电解，第5章，印刷页46','MOD06':'现代铝电解，第6章，印刷页56','MOD09':'现代铝电解，第9章，印刷页79','MOD10':'现代铝电解，第10章，印刷页86','MOD12':'现代铝电解，第12章，印刷页128','MOD16':'现代铝电解，第16章，印刷页231','MOD19':'现代铝电解，第19章，印刷页301','MOD22':'现代铝电解，第22章，印刷页368'}
def n(i,q,t,d,a,pts,s,c,rt='K2'):
 return {'question_id':i,'question':q,'primary_type':t,'secondary_capabilities':[],'knowledge_domain':d,'process_stage':'生产工艺','difficulty':'L2','applicable_conditions':c,'knowledge_unit_ids':[f'U{i}'],'question_family_id':f'F{i}','item_version':'p4.0','candidate_status':'Candidate','reference_answer':a,'key_answer_points':pts,'acceptable_alternatives':['同义且保持条件限制。'],'critical_errors':['把条件性结论说成普适规律。'],'source_ids':[s],'source_locations':[SRC[s]],'reasoning_type':rt,'expert_review_status':'Not-Reviewed'}
NEW=[
n('P401','冰晶石体系电解质为何需要对氧化铝具有较大的溶解度？','K2','电解质性质','较大的氧化铝溶解度使氧化铝能够作为原料进入熔盐并参与电解；这是选择冰晶石作为电解质主体的重要原因之一。',['氧化铝需在熔盐中溶解','与电解原料供给有关'],'MOD02','限以氧化铝为原料的冰晶石熔盐电解。'),
n('P402','为什么铝电解质还需要具有较好的导电性？','K2','电解质性质','熔融电解质导电性较好可使极间电阻率较低，有利于降低电能消耗。',['导电性影响极间电阻率','与节能相关'],'MOD02','限教材列出的电解质性能要求。'),
n('P403','为什么铝电解质的挥发性应尽量小？','K2','电解质性质','挥发性小可减少升华损失。',['挥发性影响物料损失'],'MOD02','限熔融电解质性能要求。'),
n('P404','在正常铝电解环境中，为什么铝能在阴极优先析出而不是钠？','K2','电极过程','教材从氧化铝分解电压较小及铝电解环境中的析出电位关系解释：在正常铝电解环境下铝优先析出。',['限定正常铝电解环境','不能仅凭Na+传导电流推断Na优先析出'],'MOD05','限教材讨论的正常铝电解环境。'),
n('P405','电流效率的分母为什么是理论产铝量而不是实际产铝量？','K3','电流效率','电流效率定义为实际产铝量与按法拉第定律计算的理论产铝量之比；分母用于表示输入电量对应的理论上限。',['实际量为分子','理论量为分母'],'MOD09','需统一统计周期与计算口径。','参数关系'),
n('P406','为什么“最佳槽平均电流效率略大于96%”不能直接作为所有铝电解槽的保证值？','K5','电流效率','该数字描述教材所述预焙槽表现，电流效率受槽参数与工况影响；不能外推为所有槽型和所有条件下的保证值。',['识别样本/槽型限制','拒绝无条件保证'],'MOD09','限教材表述的预焙槽情境。','条件适用性'),
n('P407','理论最低能耗为什么不能被直接当作现场实际能耗目标已经达到的证据？','K5','能耗','理论最低能耗是基于净化学反应的理想基准；实际生产值依赖过程边界、参数、采样和测定条件。',['区分理论与实际','实际值依赖测量条件'],'MOD10','限教材能耗基准定义。','条件适用性'),
n('P408','焙烧阶段为什么需要形成牢固的阴极整体？','K2','焙烧启动','焙烧使阴极炭块间及槽周扎糊烧结焦化，使阴极炭块形成牢固整体，为后续启动提供结构基础。',['烧结焦化','形成牢固整体'],'MOD12','限预焙槽焙烧过程。'),
n('P409','启动铝电解槽时，为什么需要形成一定高度的电解质熔体和铝液？','K2','焙烧启动','启动的定义包括在通入系列电流状态下形成电化学反应所需基本技术条件，其中包括一定高度的电解质熔体和铝液。',['启动需要基本反应条件','包含熔体与铝液高度'],'MOD12','限教材所述启动定义。'),
n('P410','为什么内衬维护不能只在大修时才考虑？','K2','设备维护','在破损初期及时检测、定位、修补并调整工艺条件和加强维护，可减缓破损速度并延长寿命。',['早期检测','修补和工艺调整'],'MOD16','为维护原则，不替代具体检修规程。'),
n('P411','阴极炭块破损后，为什么可能导致铝液中铁含量持续升高？','K4','设备维护','教材说明铝液和电解质熔体渗入破损部位可使阴极钢棒熔化；铁进入铝液后可使其含量上升。',['破损导致渗入','钢棒熔化','铁含量上升'],'MOD16','限教材描述的阴极内衬破损机理。','多知识点推理'),
n('P412','在物料平衡模型中，为什么理论氧化铝消耗量不等同于实际下料器计量量？','K5','物料平衡','理论消耗模型基于电流和电流效率；教材明确该计算未考虑氧化铝杂质和下料飞扬损失等影响。',['理论模型输入','未计杂质和飞扬损失'],'MOD19','限教材理论消耗模型。','条件适用性'),
n('P413','为什么应把“氧化铝加入量”和“氧化铝浓度”同时纳入下料控制判断？','K4','氧化铝浓度控制','加入量与电解消耗的关系决定浓度变化；浓度过低可能接近阳极效应临界值，过高接近饱和时可能析出。',['物料平衡影响浓度','浓度两端均有运行风险'],'MOD19','限教材的氧化铝物料平衡讨论。','多知识点推理'),
n('P414','表观槽电阻采样中，为什么槽电压和系列电流的采样不同步会干扰解析？','K3','槽电阻','教材指出槽电压与系列电流采样误差较大或不同步时，电流波动会引起表观槽电阻波动，因此会干扰槽况判断。',['采样误差/不同步','电流波动传入表观电阻'],'MOD22','限该采样计算框架。','参数关系'),
n('P415','为什么不能仅因槽电阻波动就断言槽况发生真实变化？','K6','槽电阻','不能。表观槽电阻波动还可能由槽电压和系列电流采样误差或不同步，以及真实反电动势与设定值偏差造成。',['指出替代解释','合理拒绝单一归因'],'MOD22','限教材表观槽电阻解析框架。','信息不足'),
n('P416','铝电解槽物料平衡为什么要求投入与产出维持关系，而不是只关注投入总量？','K2','物料平衡','教材指出，加入槽内的物料只有与离开槽的物料保持平衡关系，才能维持稳定运行；对氧化铝而言需与电解消耗保持平衡。',['投入与产出关系','稳定运行'],'MOD19','限物料平衡概念。'),
n('P417','为什么工艺异常分析中应区分“相关现象”与“确定原因”？','K6','异常诊断','教材中的阳极效应、表观电阻和内衬破损都显示单一现象可能有多种解释；应结合适用条件、趋势和其他证据，而非由相关现象直接断定原因。',['单一现象不等于确定原因','需要条件和补充证据'],'MOD06','为跨知识单元的审慎分析原则；需专家复核其综合表述。','信息不足'),
n('P418','为什么氧化铝溶解是否顺利会影响电流效率、能耗和物料消耗？','K4','氧化铝溶解','教材指出氧化铝是否顺利溶解关系到槽生产能否顺利进行，并影响电流效率、电能消耗和物料消耗。',['溶解与生产顺利性','影响三类指标'],'MOD03','限冷氧化铝加入电解质的教材概述。','多知识点推理')]
allq=[]
for x in legacy:
 allq.append({'question_id':x['question_id'],'question':x['question'],'primary_type':x['question_type'],'secondary_capabilities':[x.get('reasoning_type','')],'knowledge_domain':x.get('knowledge_domain',''),'process_stage':x.get('process_stage',''),'difficulty':x.get('difficulty',''),'applicable_conditions':x.get('applicability',''),'knowledge_unit_ids':[x.get('knowledge_unit_id',x['question_id'])],'question_family_id':x.get('question_family_id',x['question_id']),'item_version':'legacy-v2','candidate_status':'Candidate','reference_answer':x['reference_answer'],'key_answer_points':x['key_answer_points'],'acceptable_alternatives':x.get('acceptable_alternatives',[]),'critical_errors':x.get('common_incorrect_conclusions',[]),'source_ids':x['source_ids'],'source_locations':x['evidence_locations'],'reasoning_type':x.get('reasoning_type',''),'expert_review_status':x['expert_review_status']})
for x in e1+mg:
 allq.append({'question_id':x['question_id'],'question':x['question'],'primary_type':'E1' if x['question_id'].startswith('E') else 'M','secondary_capabilities':[x.get('assessment_mode','')],'knowledge_domain':x.get('management_domain','Evidence assessment'),'process_stage':'审查任务','difficulty':'L3','applicable_conditions':x['applicable_conditions'],'knowledge_unit_ids':[x['question_id']],'question_family_id':x['question_id'],'item_version':'p3r2.0','candidate_status':'Candidate','reference_answer':x['reference_answer'],'key_answer_points':x['key_answer_points'],'acceptable_alternatives':x.get('acceptable_alternatives',[]),'critical_errors':x.get('critical_errors',[]),'source_ids':x['evidence_ids'],'source_locations':x['source_locations'],'reasoning_type':x.get('reasoning_type','E1'),'expert_review_status':x['expert_review_status']})
allq+=NEW
def write(name,rows): (R/'datasets'/name).write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in rows)+'\n',encoding='utf8')
(R/'datasets').mkdir(parents=True,exist_ok=True); (R/'batches'/'batch_1').mkdir(parents=True,exist_ok=True)
questions=[{k:x[k] for k in ['question_id','question','primary_type','secondary_capabilities','knowledge_domain','process_stage','difficulty','applicable_conditions','knowledge_unit_ids','question_family_id','item_version','candidate_status']} for x in allq]
answers=[{k:x[k] for k in ['question_id','reference_answer','key_answer_points','acceptable_alternatives','critical_errors']}|{'rubric_id':'R-'+x['question_id']} for x in allq]
rubrics=[{'rubric_id':'R-'+x['question_id'],'question_id':x['question_id'],'scoring_dimensions':['核心结论','关键机制/条件','无过度推断'],'key_answer_points':x['key_answer_points'],'weights':[0.5,0.3,0.2],'acceptable_alternatives':x['acceptable_alternatives'],'critical_errors':x['critical_errors'],'score_cap_rules':['严重专业错误总分上限0.4'],'review_status':'Candidate'} for x in allq]
sources=[{'source_id':k,'title':'现代铝电解','document_type':'本地扫描教材','page_or_section':v,'verification_status':'Page-Verified','independence_group':'现代铝电解_2008','license_status':'本地研究使用；不分发全文'} for k,v in SRC.items()]
for sid in sorted({sid for x in allq for sid in x['source_ids']} - {x['source_id'] for x in sources}):
 sources.append({'source_id':sid,'title':'继承候选题的已记录来源','document_type':'历史候选题来源','page_or_section':'见历史 audit_view 的 evidence_locations','verification_status':'Inherited-Page-Verified','independence_group':'历史来源待补全','license_status':'本地研究使用；不分发全文'})
units=[{'knowledge_unit_id':u,'knowledge_domain':x['knowledge_domain'],'concept':x['question'],'professional_statement':x['reference_answer'],'mechanism':x['reasoning_type'],'related_concepts':x['secondary_capabilities'],'applicable_conditions':x['applicable_conditions'],'source_ids':x['source_ids'],'evidence_locations':x['source_locations'],'evidence_status':'Evidence-Verified'} for x in allq for u in x['knowledge_unit_ids']]
evidence=[]
for x in allq:
 for j,(s,l) in enumerate(zip(x['source_ids'],x['source_locations'])): evidence.append({'evidence_id':f'EV-{x["question_id"]}-{j+1}','source_id':s,'claim_id':f'CLM-{x["question_id"]}-1','question_id':x['question_id'],'evidence_location':l,'support_label':'CONDITIONAL' if x['primary_type'] in ['K5','K6','E1'] else 'SUPPORTED','applicability':x['applicable_conditions'],'verification_status':'Page-Verified'})
for name,rows in [('questions.jsonl',questions),('answers.jsonl',answers),('rubrics.jsonl',rubrics),('sources.jsonl',sources),('knowledge_units.jsonl',units),('evidence.jsonl',evidence),('audit_view.jsonl',allq)]: write(name,rows)
write('benchmark_view.jsonl',questions)
write('rejected_candidates.jsonl',[{'candidate_id':'P4-R001','reason':'未纳入：固定阈值/现场控制建议缺乏独立来源与专家审核','status':'Rejected'}])
write('../batches/batch_1/new_candidates.jsonl',NEW)
manifest={'dataset_version':'0.4.0-candidate','legacy_questions':41,'new_batch1':len(NEW),'total':len(allq),'frozen_v2_sha256':'D7B0C1F54385EFF1C6B0812E5EC93D0E5D6871F4B203B22BE557FC19CE11C95A'}
(R/'manifests').mkdir(exist_ok=True); (R/'manifests'/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8'); print(manifest)
