import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'datasets';B=R/'batches/batch_003';B.mkdir(parents=True,exist_ok=True)
src=[
 {'source_id':'EXP-07','title':'极距、槽电阻与热量耦合工程经验切片','basis':'现代铝电解第22、23、27章','tier':'A','type':'local source-linked engineering slice'},
 {'source_id':'EXP-11','title':'病槽与内衬风险的使用边界工程经验切片','basis':'铝电解技术问答第07、09、10、11章；铝电解生产技术第07章','tier':'A','type':'local source-linked engineering slice'},
 {'source_id':'EXP-12','title':'工程经验输入格式','basis':'现代铝电解第12、14、19、21–27章；铝电解生产技术第04、05章','tier':'A','type':'local source-linked engineering slice'}]
raw=[
('P7046','D07','K1','极距调节会直接影响哪些电气与热工量？','槽电阻、工作电压和焦耳发热。','极距改变电阻，进而影响电压和发热。','EXP-07'),
('P7047','D07','K5','解释槽电压或槽电阻趋势时，为什么要保留升降极方向、幅度、执行时间和阶段？','这些操作和阶段会改变趋势的物理含义；缺少事件上下文难以区分预期变化与异常候选。','趋势解释依赖事件上下文。','EXP-07'),
('P7048','D12','K4','电压或计算槽电阻变化后，工程筛查应先区分哪三类原因？','供电/基准设定造成的可计算变化、升降极等操作造成的预期变化、无相应事件可解释的残余变化。','先排除可解释变化，再评估残余。','EXP-07'),
('P7049','D12','K5','为什么“无相应操作事件的残余变化”仍不能单独确诊热状态或槽况异常？','它仅是异常候选证据，还需与温度、下料和人工巡检交叉核验。','候选信号需多源证据确认。','EXP-07'),
('P7050','D10','K6','启动期单点电压越界能否直接视为控制失败？','不能；应结合阶段、操作解释及事件后的收敛和协同信号。','单点越界不等于故障诊断。','EXP-07'),
('P7051','D12','K4','为什么要观察操作事件后的响应形状，而不是只看一个事件后的电压数值？','需判断是否在合理时间收敛、是否伴随温度或物料信号同向变化。','动态响应比孤立数值提供更多机制线索。','EXP-07'),
('P7052','D12','K5','多个槽同时出现相近电压变化时，为什么应优先核查供电、设定或数据链路？','多槽同步更可能反映共因系统问题，而不是每个槽同时发生独立槽体异常。','同步性有助于区分共因与单槽风险。','EXP-07'),
('P7053','D12','K5','什么样的电压/电阻变化会提高单槽风险的复核优先级？','单槽持续变化且无法由供电或操作事件解释时，应提高风险优先级并交叉核验。','持续性、单槽性和不可解释性共同提高风险。','EXP-07'),
('P7054','D15','K1','启动期样本至少应记录哪些类别的基础信息？','槽号槽型、内衬/焙烧路线、方案版本、时间阶段、电气与热工量、物料/电解质、操作事件及数据来源/缺失标识等。','工程样本必须同时保留工况、事件与数据质量信息。','EXP-12'),
('P7055','D15','K3','为什么特征工程要同时保留原始值和趋势值？','原始状态与1、3、6、12小时斜率/波动等趋势描述回答不同问题，不能互相替代。','状态量与变化率具有互补信息。','EXP-12'),
('P7056','D15','K6','为什么不能把缺失值静默插补为“正常”？','这样会掩盖数据新鲜度和未记录事件，可能把数据问题误作正常工况。','缺失本身是工程证据的一部分。','EXP-12'),
('P7057','D15','K5','为什么不能把操作命令时间直接作为实际执行时间？','命令与实际执行可能不一致；用命令替代执行会扭曲事件前后响应分析。','事件时间准确性影响因果/响应解释。','EXP-12'),
('P7058','D15','K5','启动期数据训练和验证为什么应按完整启动批次或槽号分组？','同一槽同一启动过程的相邻时间片高度相关，随机切分会造成信息泄漏。','分组隔离防止同过程泄漏。','EXP-12'),
('P7059','D12','K2','为什么风险输出应包含证据和待核对项，而不应直接输出控制动作？','工程经验切片将系统定位为阶段/风险/证据/复核提示工具；控制动作需由现场规程和人员决定。','筛查辅助与现场控制授权需分离。','EXP-12'),
('P7060','D12','K5','病槽或内衬风险筛查中，哪些表现可作为入口而非确诊？','持续电气不稳、热工不均、物料响应失配或操作后长期不回稳可触发筛查，但不等于确诊。','风险入口与诊断结论不同。','EXP-11'),
('P7061','D12','K4','风险分诊中“提示”“复核”“升级”三层如何区分？','提示为单变量异常且有合理解释；复核为多变量一致偏移或响应异常；升级为触及安全/设备边界、疑似内衬损伤、强异常电压或数据不足以安全判断。','风险层级由证据强度和安全边界共同决定。','EXP-11'),
('P7062','D12','K5','为什么不能用“任何异常曲线”作为病槽训练标签？','标签应来自事后确认记录和检修结论；否则模型可能学习传感器故障或人工操作特征并误报。','标签真实性决定模型学习对象。','EXP-11')]
Q=[]
for i,d,t,q,a,m,s in raw:Q.append({'question_id':i,'question':q,'primary_type':t,'knowledge_domain':d,'reference_answer':a,'key_answer_points':[a],'necessary_mechanism':m,'applicable_conditions':'限启动期工程筛查、趋势解释或数据集构建；不替代本厂异常规程。','source_ids':[s],'evidence_locations':[next(x['basis'] for x in src if x['source_id']==s)],'evidence_tier':'A','evidence_limitations':'来源为本地教材章节关联的工程经验切片；需专家审核后方可作正式规程。','review_status':'Not-Reviewed','expert_review_status':'Not-Reviewed','question_family_id':'P7B3F'+i[-2:],'rubric_id':'R-'+i,'reasoning_steps':[m],'critical_errors':['将筛查信号写为确定诊断','将风险提示写为自动控制指令'],'acceptable_alternatives':['保持工程筛查边界的同义表述。'],'candidate_status':'Candidate'})
def w(n,x):(D/n).write_text('\n'.join(json.dumps(y,ensure_ascii=False) for y in x)+'\n',encoding='utf8')
w('batch003_questions.jsonl',Q);w('batch003_answers.jsonl',[{k:x[k] for k in ['question_id','reference_answer','key_answer_points','necessary_mechanism','applicable_conditions','critical_errors']} for x in Q]);w('batch003_rubrics.jsonl',[{'rubric_id':x['rubric_id'],'question_id':x['question_id'],'dimensions':['工程结论','机制','适用边界','安全错误限制']} for x in Q]);w('batch003_sources.jsonl',src);w('batch003_evidence.jsonl',[{'evidence_id':'EV-'+x['question_id'],'question_id':x['question_id'],'source_id':x['source_ids'][0],'tier':'A','location':x['evidence_locations'][0]} for x in Q])
for f in D.glob('batch003_*.jsonl'):(B/f.name).write_text(f.read_text(encoding='utf8'),encoding='utf8')
s=json.loads((R/'BUILD_STATE.json').read_text(encoding='utf8'));s.update({'current_candidate_count':135+len(Q),'accepted_candidate_count':45+len(Q),'review_ready_count':43+len(Q),'completed_batches':['P7-batch_001','P7-batch_002','P7-batch_003'],'next_batch_id':'P7-batch_004','last_validation_result':'pending','next_tasks':['OCR and page-verify additional chapters from 铝电解技术问答; family-level review before split.']});(R/'BUILD_STATE.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf8');print({'new':len(Q),'total':s['current_candidate_count']})
