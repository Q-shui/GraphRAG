import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'datasets';D.mkdir(parents=True,exist_ok=True)
base=Path(r'C:\科研\agent\文献\电解铝\可直接输入工程经验切片')
S=[
 {'book_id':'B01','title':'现代铝电解','authors':'刘业翔等编著（PDF元数据）','publisher':'Unknown','publication_year':'2008（文件名）','format':'PDF','page_count':650,'text_layer':'not verified; command-line extraction unavailable','status':'catalogued; no newly page-verified content in P8'},
 {'book_id':'B02','title':'铝电解生产技术','authors':'杨升、杨冠群编著（PDF元数据）','publisher':'Unknown','publication_year':'Unknown','format':'PDF','page_count':260,'text_layer':'not verified; command-line extraction unavailable','status':'catalogued; no newly page-verified content in P8'},
 {'book_id':'B03','title':'铝电解技术问答','authors':'杨升、杨冠群编著（PDF元数据）','publisher':'Unknown','publication_year':'Unknown','format':'PDF','page_count':284,'text_layer':'not verified; command-line extraction unavailable','status':'catalogued; no newly page-verified content in P8'}]
items=[
('T801','K1','槽电阻与极距','极距调节会直接影响哪些量？','槽电阻、工作电压和焦耳发热。','B01','第22、23、27章'),('T802','K5','趋势解释','为什么解释电压趋势要同时知道极距动作方向和阶段？','极距动作和阶段会改变趋势含义，缺事件上下文难以分开预期变化和异常候选。','B01','第22、23、27章'),('T803','K4','异常筛查','电压或电阻变化后应优先排查哪三类原因？','供电/设定变化、操作造成的预期变化、无相应事件解释的残余变化。','B01','第22、23、27章'),('T804','K6','异常筛查','残余电阻变化能否单独确诊槽况异常？','不能，还需温度、下料和人工巡检交叉核验。','B01','第22、23、27章'),('T805','K5','启动管理','启动期单点电压越界为何不等于控制失败？','需观察阶段、操作解释和事件后收敛/协同信号。','B01','第22、23、27章'),('T806','K4','响应分析','为什么要看操作后的响应形状？','是否收敛及是否伴随温度/物料同向变化能提供机制线索。','B01','第22、23、27章'),('T807','K5','系统诊断','多槽同步变化时为何优先核查系统共因？','同步性更可能提示供电、设定或数据链路问题。','B01','第22、23、27章'),('T808','K1','数据记录','启动期样本应记录哪些类别信息？','槽型与方案、阶段、电气热工量、物料电解质、操作事件及来源/缺失标识。','B02','第04、05章'),('T809','K3','数据特征','为什么应同时保留原始值和趋势值？','状态量与变化率回答不同问题，具有互补信息。','B02','第04、05章'),('T810','K6','数据质量','为什么不能把缺失值静默填为正常？','会掩盖数据质量和未记录事件，导致错误解释。','B02','第04、05章'),('T811','K5','事件记录','为什么不能用操作命令时间代替实际执行时间？','二者可能不一致，会扭曲事件前后响应分析。','B02','第04、05章'),('T812','K5','数据泄漏','为什么启动期训练验证要按槽号或完整启动批次分组？','相邻时间片高度相关，随机划分会泄漏同一过程信息。','B02','第04、05章'),('T813','K2','风险输出','为什么风险系统应输出证据和待核对项而不直接下控制指令？','筛查辅助与现场控制授权需分离。','B02','第04、05章'),('T814','K5','病槽筛查','哪些表现可作为病槽或内衬风险的筛查入口？','持续电气不稳、热工不均、物料响应失配或操作后长期不回稳。','B03','第07、09、10、11章'),('T815','K4','风险分诊','提示、复核、升级如何区分？','分别对应可解释单变量异常、多变量一致偏移/响应异常、触及安全设备边界或无法安全判断。','B03','第07、09、10、11章'),('T816','K5','标签治理','为什么任何异常曲线不能直接作为病槽标签？','否则可能学习传感器故障或人工操作特征；标签应来自事后确认记录和检修结论。','B03','第07、09、10、11章')]
Q=[]
for i,t,d,q,a,b,p in items:Q.append({'question_id':i,'question':q,'primary_type':t,'knowledge_domain':d,'reference_answer':a,'key_answer_points':[a],'necessary_concepts':[d],'applicable_conditions':'限工程经验切片标明的启动期筛查、趋势解释或风险分诊语境；不替代现场规程。','source_ids':[b],'evidence_locations':[p],'evidence_status':'TEXTBOOK_VERIFIED','difficulty':'L2' if t in ['K1','K2'] else 'L3','review_status':'Candidate','expert_review_status':'Not-Reviewed','knowledge_unit_id':'KU-'+i,'question_family_id':'P8F'+i[-2:],'rubric_id':'R-'+i})
def w(n,x):(D/n).write_text('\n'.join(json.dumps(z,ensure_ascii=False) for z in x)+'\n',encoding='utf8')
old_ids=list(range(7046,7063))
rejected=[]
for x,old_id in zip(Q,old_ids):
    y=dict(x)
    y.update({'candidate_status':'REJECTED','rejection_reason':'与KQA-P7 batch_003 语义重复；本轮不得以教材来源重收录历史候选题。','duplicate_of_question_id':f'P{old_id}','evidence_status':'REJECTED'})
    rejected.append(y)
new=[
('T801','K1','铝电解环境负荷','铝电解生产过程涉及哪些主要类别的污染或废物？','温室气体和全氟化物、有害气体、含氟粉尘/氧化铝粉尘/炭粉、沥青挥发物以及含氟废旧阴极内衬。','457','TEXTBOOK_VERIFIED'),
('T802','K2','铝电解环境负荷','为什么处理铝电解环境问题不能只关注烟气中的一种污染物？','教材列出的环境负荷同时包括气体、粉尘、挥发物和含氟废内衬；不同介质和来源需要分别识别与处理。','457','TEXTBOOK_VERIFIED'),
('T803','K5','环境比较边界','能否把教材给出的铝与钢的单位能耗和CO₂排放比较，直接当作所有地区和时期的固定结论？','不能。该比较是教材在特定统计背景下的表述；用于其他地区、技术或时期时应复核统计边界和数据来源。','457','INFERENCE_REVIEW_REQUIRED'),
('T804','K1','生命周期环境负荷','分析铝电解环境负荷时，为什么要把铝土矿开采、氧化铝生产、阳极生产和电解过程放在同一生命周期中考察？','教材指出需了解各工序的直接和间接环境负荷及来源，才能识别铝电解在整个铝工业环境负荷中的位置并提出针对性措施。','457','TEXTBOOK_VERIFIED'),
('T805','K3','能耗边界','教材以能耗分析环境负荷时，为什么不能只把电解槽现场直接排放作为全部环境负荷？','电解环境负荷还包括因能源消耗形成的直接与间接负荷，以及物料消耗带来的间接负荷。','458','NEEDS_PAGE_REVIEW'),
('T806','K4','环境改进机制','为什么降低电解过程环境负荷既要改进电解工艺，也要考虑电力结构和发电效率？','教材指出除CO₂和氟化物外，能源消耗相关负荷大于工艺本身负荷；因此仅改进槽内工艺不能覆盖全部来源。','460','NEEDS_PAGE_REVIEW'),
('T807','K1','氟化物污染源','铝电解烟气中氟化物可能来自哪些过程或物料？','教材列出电解质蒸气、由水分反应生成的气态HF、接近阳极效应时的全氟化物，以及添加氟化盐飞扬形成的含氟粉尘。','460','NEEDS_PAGE_REVIEW'),
('T808','K2','氟化物形成','为什么原料或空气带入的水分会成为气态HF来源的关注对象？','教材给出水分与电解质组分反应生成HF的反应式，因此水分参与可形成气态氟化物来源。','460','NEEDS_PAGE_REVIEW'),
('T809','K1','阳极效应环境负荷','教材将哪些含氟温室气体与接近阳极效应的状态相联系？','教材将CF₄和C₂F₆与电解过程接近阳极效应时产生的全氟化物相联系。','460','NEEDS_PAGE_REVIEW'),
('T810','K2','固体废物管理','为什么大修拆出的电解槽内衬不能按一般惰性固废简单处置？','教材指出废内衬除含大量氟化物外还含一定量氰化物，必须专门处理。','461','NEEDS_PAGE_REVIEW'),
('T811','K4','固废贮存边界','为什么废内衬处理后的堆场仍需要具备防止地下水污染的性能？','教材要求废渣堆放在专门设置的堆场并防止地下水污染；处理并不自动消除贮存阶段的环境风险。','461','INFERENCE_REVIEW_REQUIRED'),
('T812','K1','残极环境负荷','什么是预焙阳极残极，为什么它与氟化物管理有关？','残极是预焙阳极未被完全消耗的剩余部分；教材说明其带有一定量电解质，并会带走以氟计的物质。','461','NEEDS_PAGE_REVIEW'),
('T813','K2','氟化物与作物','大气氟化物可通过哪些途径进入植物，并可能造成什么类型的影响？','教材说明气态氟化物可经叶片气孔进入，颗粒物可沉积在叶面；过量吸收可出现叶褪绿、叶端坏死并影响生长和产量。','462','NEEDS_PAGE_REVIEW'),
('T814','K5','植物氟暴露','能否仅按一种作物的反应判断所有作物对氟化物的敏感性？','不能。教材明确不同植物以及同一植物的不同生长期对氟化物敏感性差异很大。','462','NEEDS_PAGE_REVIEW'),
('T815','K1','排放标准概念','污染物排放标准中的最高允许排放浓度、最高允许排放速率和无组织排放监控浓度限值分别服务于什么管理对象？','教材将它们列为综合排放标准中的不同控制指标；其中最高排放速率具有总量控制意义。','463','NEEDS_PAGE_REVIEW'),
('T816','K6','法规时效边界','能否将教材列举的1996—2002年环境标准和法律名称，直接当作今天的现行合规清单？','不能。本题教材只可说明当时的标准体系及其历史表述；当前合规要求必须另查现行法规，不能由旧教材替代。','463-464','INFERENCE_REVIEW_REQUIRED')]
def mk(t):
 i,k,d,q,a,p,st=t
 return {'question_id':i,'question':q,'primary_type':k,'knowledge_domain':d,'reference_answer':a,'key_answer_points':[a],'necessary_concepts':[d],'applicable_conditions':'限《现代铝电解》第29章所述环境负荷与污染控制语境；不替代当前法规、现场规程或医学判断。','acceptable_alternatives':['不超出教材证据与适用边界的同义表述。'],'common_errors':['把历史教材标准写成当前合规结论','把污染来源或风险提示写成单一确定归因'],'source_ids':['B01'],'chapter_id':'B01-C29','evidence_locations':[f'现代铝电解，第29章，印刷页{p}；PDF页{int(p.split("-")[0])-456}'],'evidence_status':st,'difficulty':'L2' if k in ['K1','K2'] else 'L3','review_status':'Candidate','expert_review_status':'Not-Reviewed','knowledge_unit_id':'KU-'+i,'question_family_id':'P8-C29-'+i[-2:],'rubric_id':'R-'+i}
Q=[mk(t) for t in new]
w('textbook_sources.jsonl',S);w('textbook_questions.jsonl',Q);w('textbook_answers.jsonl',[{k:x[k] for k in ['question_id','reference_answer','key_answer_points','necessary_concepts','applicable_conditions','acceptable_alternatives','common_errors']} for x in Q]);w('textbook_rubrics.jsonl',[{'rubric_id':x['rubric_id'],'question_id':x['question_id'],'scoring_dimensions':['核心结论','教材支持的机制或分类','适用边界'],'points':[5,3,2],'full_credit_criteria':'覆盖参考答案的核心结论且不越过教材边界','critical_errors':x['common_errors']} for x in Q]);w('textbook_knowledge_units.jsonl',[{'knowledge_unit_id':x['knowledge_unit_id'],'book_id':'B01','chapter_id':'B01-C29','concept_name':x['knowledge_domain'],'knowledge_statement':x['reference_answer'],'source_page':x['evidence_locations'][0],'evidence_status':x['evidence_status'],'importance':'high','question_potential':'used'} for x in Q]);w('textbook_evidence.jsonl',[{'evidence_id':'EV-'+x['question_id'],'question_id':x['question_id'],'book_id':'B01','chapter_id':'B01-C29','location':x['evidence_locations'][0],'ocr_file':f'batches/batch_001/ocr/B01_C29-{int(x["evidence_locations"][0].split("印刷页")[1].split("；")[0].split("-")[0])-456:02}.txt','status':x['evidence_status']} for x in Q]);w('textbook_audit_view.jsonl',Q+rejected);w('textbook_benchmark_view.jsonl',[x for x in Q if x['evidence_status']=='TEXTBOOK_VERIFIED']);w('pending_review.jsonl',[x for x in Q if x['evidence_status']!='TEXTBOOK_VERIFIED']);w('rejected_candidates.jsonl',rejected)
(R/'BUILD_STATE.json').write_text(json.dumps({'books':S,'processed_chapters':['B01-C29 pages 457–464: OCR saved; visual cross-check completed only for page 457'],'new_questions':len(Q),'textbook_verified':sum(x['evidence_status']=='TEXTBOOK_VERIFIED' for x in Q),'pending_page_review':sum(x['evidence_status']!='TEXTBOOK_VERIFIED' for x in Q),'rejected_as_history_duplicates':len(rejected),'next_batch':'visually verify pages 458–464 before promoting pending candidates; then OCR a non-overlapping chapter'},ensure_ascii=False,indent=2),encoding='utf8')
print({'accepted_questions':len(Q),'textbook_verified':sum(x['evidence_status']=='TEXTBOOK_VERIFIED' for x in Q),'rejected_duplicates':len(rejected),'sha256':hashlib.sha256((D/'textbook_questions.jsonl').read_bytes()).hexdigest().upper()})
