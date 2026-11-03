# 数据集 Schema 与版本治理

主问题表只保留稳定题目 ID、题干、能力、条件、知识单元和家族。答案/评分表保存答案与关键点；证据表保存 source/evidence/claim/link/label；审阅表保存 reviewer、轮次、决定和意见；治理表保存版本、变更、风险、许可、替代关系。

关系：`Question 1-n Claim`，`Claim n-m Evidence`，`Question 1-n Review`，`Question 1-n Change`。评测模型只见 Question View；评分者见 Answer/Rubric；证据模式 B 仅见授权 Evidence View；Review/Governance 不进入模型上下文。

变更规则：题干改写若改变对象、条件或可接受解释，重审受影响主张；答案机制修改必做知识单元反向索引，复查共享该单元的题；只改版式可记录为非语义变更。旧内容 append-only 保存，`superseded_by` 指向新版本。
