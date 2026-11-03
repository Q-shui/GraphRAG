import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'datasets';B=R/'batches/batch_002';B.mkdir(parents=True,exist_ok=True)
items=[
('P7026','D04','K1','冷氧化铝进入电解质后可能有哪些不同去向？','可溶解，也可能结成面壳/炉帮或沉落槽底形成沉淀。','物料去向取决于溶解与运行条件。'),
('P7027','D04','K3','氧化铝能否顺利溶解，为什么不能只看加料量？','还受氧化铝品种性质、电解质性质和状态、加料方式影响。','溶解由颗粒、熔盐和加料过程共同影响。'),
('P7028','D07','K1','现代预焙电解槽的四个结构大类是什么？','阴极结构、上部结构、母线结构和电气绝缘。','结构分层服务于电流、热和机械功能。'),
('P7029','D05','K1','阳极效应发生时除电压变化外可观察哪些类别现象？','可有阳极周围火花/声响、电解质状态变化和气体组成变化等。','异常会伴随多维信号。'),
('P7030','D07','K2','为什么槽电压与系列电流采样不同步会干扰表观电阻判断？','不同步或误差会让电流波动映射为表观电阻波动，未必代表真实槽况变化。','派生量受输入采样误差传播。'),
('P7031','D07','K6','发现表观槽电阻波动，能否直接断言槽况真实变化？','不能；还应排查电压/电流采样误差、同步性和反电动势设定偏差。','测量伪差与工况变化需区分。'),
('P7032','D11','K3','为何一点测定适合日常粗略了解而多点测定适合技术管理？','多点提供更全面信息，可用于技术条件管理、出铝量决定或临时全面分析。','采样密度改变信息代表性。'),
('P7033','D03','K2','正常铝电解中阴极主要过程及副过程有哪些？','主要为铝析出；教材列出钠析出和铝溶解为副过程。','阴极反应并非只有单一过程。'),
('P7034','D03','K5','为何不能将水溶液中的析出顺序直接套用于熔盐铝电解？','含大量H+水溶液中氢会优先析出；熔盐铝电解的介质与电极过程不同。','介质组成改变竞争反应。'),
('P7035','D13','K5','“最佳槽平均电流效率略大于96%”能否用作所有槽型保证值？','不能；该值有教材所述槽型与工况边界。','性能指标必须带技术条件。'),
('P7036','D10','K1','启动电解槽形成基本电化学条件时，液相高度为何是组成部分？','启动需在通电下形成一定高度的电解质熔体和铝液，才具备基本反应条件。','液层结构是启动工况的一部分。'),
('P7037','D06','K2','阴极炭块破损为何可能使铝液铁含量出现持续上升趋势？','铝液和熔体渗入破损处可能使阴极钢棒熔化，铁进入铝液。','破损可改变材料接触与迁移路径。'),
('P7038','D08','K3','为何物料平衡不应只记录投入总量？','稳定运行要求进入槽内的物料与离开槽的物料保持关系，对氧化铝还需对应电解消耗。','平衡是输入与输出关系。'),
('P7039','D04','K2','氧化铝溶解不顺利为何会牵连电流效率、能耗和物耗？','教材指出其会影响生产顺利性，并影响电流效率、电耗和物料消耗。','原料传质/溶解影响过程绩效。'),
('P7040','D15','K5','为什么能耗分析记录不能只保存一个数值？','还要保留度量体系、测定基准、系统边界和量纲，才能解释和比较差异。','可追溯口径是工程比较前提。'),
('P7041','D12','K4','若电压升高且氧化铝加入长期不足，为什么仍不应省略浓度与持续时间判断？','不足会降低浓度，但是否达到临界值以及电压变化的原因仍需浓度、时间和工况证据。','多线索不等于自动因果确证。'),
('P7042','D16','K5','为什么不同槽型的结构差异会限制操作经验的直接迁移？','不同槽工艺制度下结构可明显不同，操作与控制经验需核查其技术条件。','技术结构与制度共同决定适用性。'),
('P7043','D02','K1','电解质挥发性应尽量小的直接工程原因是什么？','挥发性小有助于减少升华损失。','物质挥发导致物料损失。'),
('P7044','D03','K2','正常铝电解环境中为何铝可优先于钠在阴极析出？','教材按氧化铝分解电压和铝电解环境中的析出电位关系解释铝优先析出。','析出顺序由体系电化学条件决定。'),
('P7045','D06','K6','只有“铝液铁升高”这一条信息时，诊断内衬故障还缺什么？','缺少连续趋势、硅变化、其他铁来源和运行背景；不能据单点指标确证。','故障诊断需排除替代解释。')]
def full(i):
 q,dom,t,qu,ans,m=i
 return {'question_id':q,'question':qu,'primary_type':t,'knowledge_domain':dom,'reference_answer':ans,'key_answer_points':[ans],'applicable_conditions':'限已核验教材章节的原料、槽型和运行语境。','source_ids':['MOD-PAGE-VERIFIED'],'evidence_locations':['P4 已登记页级来源；P7 batch_002继承使用'],'evidence_tier':'A','evidence_limitations':'单一页级核验教材来源；未专家审核。','review_status':'Not-Reviewed','expert_review_status':'Not-Reviewed','question_family_id':'P7B2F'+q[-2:],'rubric_id':'R-'+q,'reasoning_steps':[m],'critical_errors':['把条件性结论写为无条件规则。'],'acceptable_alternatives':['不超出来源范围的同义表述。'],'candidate_status':'Candidate'}
Q=[full(x) for x in items]
def w(n,x): (D/n).write_text('\n'.join(json.dumps(y,ensure_ascii=False) for y in x)+'\n',encoding='utf8')
w('batch002_questions.jsonl',Q);w('batch002_answers.jsonl',[{k:x[k] for k in ['question_id','reference_answer','key_answer_points','applicable_conditions','reasoning_steps','critical_errors','acceptable_alternatives']} for x in Q]);w('batch002_rubrics.jsonl',[{'rubric_id':x['rubric_id'],'question_id':x['question_id'],'dimensions':['结论','机理/关系','条件','错误限制']} for x in Q]);w('batch002_evidence.jsonl',[{'evidence_id':'EV-'+x['question_id'],'question_id':x['question_id'],'source_id':'MOD-PAGE-VERIFIED','tier':'A'} for x in Q])
for f in D.glob('batch002_*.jsonl'):(B/f.name).write_text(f.read_text(encoding='utf8'),encoding='utf8')
s=json.loads((R/'BUILD_STATE.json').read_text(encoding='utf8'));s.update({'current_candidate_count':115+len(Q),'accepted_candidate_count':25+len(Q),'review_ready_count':23+len(Q),'evidence_limited_count':2,'completed_batches':['P7-batch_001','P7-batch_002'],'next_batch_id':'P7-batch_003','last_validation_result':'pending','next_tasks':['Acquire new full text for D09 and D12; merge after family-level audit.']});(R/'BUILD_STATE.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf8');print({'new':len(Q),'total':s['current_candidate_count']})
