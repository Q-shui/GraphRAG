# 第一轮审查复现记录

## 执行边界

- 执行日期：2026-10-22（Asia/Shanghai）。
- 本轮仅读取既有知识题候选集及其审查材料；未读取运行数据、未生成运行数据题，未执行 LLM、RAG、Agent 或训练任务。
- 本地改造方案：用 `scripts/build_v1_rewrite.py` 从冻结的旧候选集生成独立表述的 v1 候选集与逐题审查清单；不写回旧候选集。

## 命令与结果（代码事实）

```powershell
python knowledge_qa_only/scripts/build_v1_rewrite.py
python knowledge_qa_only/validation/test_v1_rewrite.py
Get-FileHash 'P2_dual_track/P2_MVP/datasets/knowledge_qa_candidates.jsonl' -Algorithm SHA256
Get-FileHash 'knowledge_qa_only/datasets/knowledge_qa_v1_candidates.jsonl' -Algorithm SHA256
```

输出摘要：

```text
{\"old\": 15, \"new\": 13, \"decisions\": {\"RETAIN\": 1, \"REWRITE\": 12, \"MERGE\": 0, \"REJECT\": 2}}
PASS: independent wording screen, decisions, 13 non-rejected candidates, no inherited verification after rewrite
```

## 哈希与解释

| 文件 | SHA-256 | 结论 |
|---|---|---|
| `P2_dual_track/P2_MVP/datasets/knowledge_qa_candidates.jsonl` | `5AFE305C47BE0BE0E8DE42EB695F1A5417F931B79C5CF240EAB8307C76E6F88F` | 冻结的 15 题旧文件未被本轮改写。 |
| `datasets/knowledge_qa_v1_candidates.jsonl` | `4105757845C9FFD0AA1DD832D0798DEC3877C8E07752CB78878646F0A875D73A` | 本轮生成的 13 题 v1 候选集。 |

测试仅证明表述筛查、决策数量和状态继承规则通过；不能替代来源证据复核或领域专家审批。
