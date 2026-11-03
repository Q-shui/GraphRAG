import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'datasets';B=R/'batches/batch_001'
for x in [D,B,R/'validation',R/'manifests']:x.mkdir(parents=True,exist_ok=True)
K=R.parent
src=[{'source_id':'MOD-PAGE-VERIFIED','title':'现代铝电解（已核验页级章节）','type':'local professional textbook','access':'page-verified local research copy','tier':'A'},{'source_id':'P6-IPCC-2019','title':'IPCC 2019 Refinement Ch4','type':'guideline','access':'full text','tier':'A'},{'source_id':'P6-ICSOBA-2025-AL16','title':'Wireless and Automated Preheat Monitoring','type':'industrial conference case','access':'full PDF','tier':'A'},{'source_id':'P6-SINTEF-2017-CATHODE','title':'Cathode wear based on autopsy','type':'academic publication page','access':'abstract','tier':'B'},{'source_id':'P6-SINTEF-2015-PAE','title':'Laboratory study of partial anode effects','type':'academic publication page','access':'abstract','tier':'B'}]
base=[
('D01','K1','电解质为何既要导电又要溶解氧化铝？','它既是离子导电介质，又要使氧化铝进入熔盐并参与电解。','电解质的导电与溶解功能。','MOD-PAGE-VERIFIED','A'),
('D02','K3','为何电解质密度应低于熔融铝？','较轻电解质位于铝液上方，可保护铝液并有利于槽内分层。','密度差形成液层分层。','MOD-PAGE-VERIFIED','A'),
('D03','K2','冷氧化铝加入后为何会改变槽热状态？','溶解吸热且冷颗粒需升温，会从体系吸收热量。','显热和溶解热需求。','MOD-PAGE-VERIFIED','A'),
('D04','K5','为何下料控制既要避免长期不足也要避免长期过量？','不足会使浓度降低并接近阳极效应临界条件；过量接近饱和时可能析出沉积。','加入量与消耗共同决定浓度。','MOD-PAGE-VERIFIED','A'),
('D04','K3','理论氧化铝消耗量为何不能直接等同于下料器的实际计量量？','理论模型基于电流和电流效率，未计入杂质和飞扬等实际损失。','理论物料平衡与现场计量边界不同。','MOD-PAGE-VERIFIED','A'),
('D05','K6','只观察到槽电压上升，能否单独确认阳极效应？','不能；电压上升是典型现象之一，仍需结合其他特征和运行语境。','单一信号不是充分诊断证据。','MOD-PAGE-VERIFIED','A'),
('D06','K5','铝液中铁和硅一次升高能否确认内衬破损？','不能；连续趋势和组合线索更具提示性，单次升高解释不唯一。','趋势与组合证据优于单点现象。','MOD-PAGE-VERIFIED','A'),
('D06','K2','为何内衬早期破损需检测、定位和修补？','早期处置及工艺调整可减缓破损并有助于延长寿命。','失效早期干预可限制损伤发展。','MOD-PAGE-VERIFIED','A'),
('D07','K3','为何表观槽电阻解析需同时记录槽电压和系列电流？','给定模型中R0由(U-B)/I计算，电压或电流信息缺失无法得到该表观量。','表观电阻由电压、电流和设定反电动势共同定义。','MOD-PAGE-VERIFIED','A'),
('D07','K5','为何不能把任意工况的表观槽电阻视为真实槽电阻？','设定B未必等于真实反电动势，二者相等才满足该解释条件。','模型常数与真实状态的偏差限制解释。','MOD-PAGE-VERIFIED','A'),
('D08','K5','为何比较能耗报告需先统一系统边界和测定基准？','相同单位不能消除边界、度量体系和基准差异，未统一时数值不可直接比较。','比较需要相同口径。','MOD-PAGE-VERIFIED','A'),
('D08','K1','电流效率在物理量关系上表达什么？','表达实际产铝量与按法拉第定律计算的理论产铝量之比。','实际产出相对理论上限。','MOD-PAGE-VERIFIED','A'),
('D10','K1','焙烧对阴极结构和槽膛状态的直接目的是什么？','使扎糊烧结焦化形成牢固整体，并烘干内衬、逐步升温，为启动准备。','结构形成与热状态准备。','MOD-PAGE-VERIFIED','A'),
('D10','K5','为何启动后非正常期不能按所有槽型给固定时长？','该过渡期受槽型、运行条件和技术方案影响。','启动过程具有条件依赖性。','MOD-PAGE-VERIFIED','A'),
('D11','K1','大型预焙槽常规生产中哪些作业仍可能需人工或天车配合？','所述条件下包括换阳极、出铝、抬母线及液位测量等。','自动化水平和作业方式取决于具体技术条件。','MOD-PAGE-VERIFIED','A'),
('D12','K5','为何异常分析不能把相关现象直接当作确定原因？','阳极效应、电阻波动和内衬线索均可能有多种解释，需要条件、趋势和其他证据。','相关性不等于因果诊断。','MOD-PAGE-VERIFIED','A'),
('D13','K2','为何电解质导电性会影响电能消耗？','较好导电性有助于降低极间电阻率，从而有利于降低电耗。','电阻率影响电压降和能耗。','MOD-PAGE-VERIFIED','A'),
('D13','K5','为何理论最低能耗不能证明现场已经达到该能耗？','理论值是理想化学反应基准，实际值还依赖过程边界、参数、采样和测定。','理论基准与现场实测不同。','MOD-PAGE-VERIFIED','A'),
('D14','K5','为何同样的阳极效应分钟数据不能脱离槽型直接比较PFC排放？','系数和活动数据可随技术及设施定义而不同，需明确核算方法和适用条件。','技术特异排放核算。','P6-IPCC-2019','A'),
('D15','K3','一点测定与多点测定在技术条件管理中的用途为何不同？','一点测定用于日常粗略了解变化；多点测定用于管理、决定出铝量或全面分析等。','测点数量决定信息分辨率和用途。','MOD-PAGE-VERIFIED','A'),
('D16','K5','为何不能将某一200kA中心下料预焙槽的结构图当作所有工业槽的通用结构？','不同槽型和工艺制度下各部分结构可有较大差异。','案例槽型与通用结构应区分。','MOD-PAGE-VERIFIED','A'),
('D06','E1','单座2461天服役的阴极尸检能否给出所有槽型的寿命结论？','不能；它支持特定材料和该槽的磨损观察，不支持通用寿命或唯一机理。','单案例外推边界。','P6-SINTEF-2017-CATHODE','B'),
('D05','E1','双阳极低氧化铝实验能否直接证明工业大槽的全部局部阳极效应机制？','不能；它是特定实验装置，只能提供实验线索。','实验尺度与工业槽边界不同。','P6-SINTEF-2015-PAE','B'),
('D10','K4','为何预热质量不能只用最终平均温度评价？','案例还关注温度分布、垂直梯度、升温速率和电流分布；平均值不能代表热均匀性。','空间和时间温度条件共同影响预热状态。','P6-ICSOBA-2025-AL16','A'),
('D10','K6','仅知“预热结束”能否判断可安全浴液加入？','不能；仍需温度、分布/梯度、升温过程和本槽程序条件。','转换决策需要多项状态信息。','P6-ICSOBA-2025-AL16','A')]
# second capability question for distinct, family-bound units
Q=[]
for j,(dom,t,qu,ans,mech,source,tier) in enumerate(base,1):
 i=f'P7{j:03d}';Q.append({'question_id':i,'question':qu,'primary_type':t,'knowledge_domain':dom,'reference_answer':ans,'key_answer_points':[ans],'applicable_conditions':'限所列来源的工艺/模型/案例边界。','source_ids':[source],'evidence_locations':['见来源登记'],'evidence_tier':tier,'evidence_limitations':'单一来源；B级为摘要或单案例，不得外推。' if tier=='B' else '单一可定位来源，未完成专家审核。','review_status':'Not-Reviewed','expert_review_status':'Not-Reviewed','question_family_id':'P7F'+str(j),'rubric_id':'R-'+i,'reasoning_steps':[mech],'critical_errors':['无条件跨槽型推广','把案例或实验写成普适规律'],'acceptable_alternatives':['不超出适用范围的同义专业表述。'],'candidate_status':'Candidate'})
# add 15 P6 items as historical import mapping only, not duplicate P7 data; P7 current new=25
def w(n,x): (D/n).write_text('\n'.join(json.dumps(y,ensure_ascii=False) for y in x)+'\n',encoding='utf8')
w('questions.jsonl',[{k:v for k,v in x.items() if k not in ['reference_answer','key_answer_points','reasoning_steps','critical_errors','acceptable_alternatives']} for x in Q]);w('answers.jsonl',[{k:x[k] for k in ['question_id','reference_answer','key_answer_points','applicable_conditions','reasoning_steps','critical_errors','acceptable_alternatives']} for x in Q]);w('rubrics.jsonl',[{'rubric_id':x['rubric_id'],'question_id':x['question_id'],'dimensions':['核心结论','必要机理/关系','适用条件','避免过度推广'],'critical_errors':x['critical_errors']} for x in Q]);w('sources.jsonl',src);w('knowledge_units.jsonl',[{'knowledge_unit_id':'KU-'+x['question_id'],'knowledge_domain':x['knowledge_domain'],'core_claim':x['reference_answer'],'source_ids':x['source_ids'],'evidence_tier':x['evidence_tier'],'limitations':x['evidence_limitations']} for x in Q]);w('evidence.jsonl',[{'evidence_id':'EV-'+x['question_id'],'question_id':x['question_id'],'source_id':x['source_ids'][0],'tier':x['evidence_tier'],'location':x['evidence_locations'][0]} for x in Q]);w('benchmark_view.jsonl',Q);w('audit_view.jsonl',Q);w('pending_candidates.jsonl',[]);w('rejected_candidates.jsonl',[])
for n in ['questions','answers','rubrics','sources','knowledge_units','evidence','benchmark_view','audit_view','pending_candidates','rejected_candidates']:(B/(n+'.jsonl')).write_text((D/(n+'.jsonl')).read_text(encoding='utf8'),encoding='utf8')
state={'current_candidate_count':90+len(Q),'accepted_candidate_count':len(Q),'review_ready_count':sum(x['evidence_tier']=='A' for x in Q),'evidence_limited_count':sum(x['evidence_tier']=='B' for x in Q),'pending_evidence_count':0,'completed_batches':['P7-batch_001'],'next_batch_id':'P7-batch_002','covered_domains':sorted(set(x['knowledge_domain'] for x in Q)),'pending_domains':['D09','D11','D12'],'source_registry_version':'P7.1','data_version':'P7-batch001','last_validation_result':'pending','next_tasks':['Find full texts for D09/D11/D12; review semantic families before split.']}
(R/'BUILD_STATE.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8');print(state)
