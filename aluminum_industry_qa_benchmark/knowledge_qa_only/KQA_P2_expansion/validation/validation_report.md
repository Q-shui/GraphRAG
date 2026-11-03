# KQA-P2 可复现验证记录

- 时间：2026-10-22（Asia/Shanghai）
- 边界：未读取或使用真实生产运行数据；未启动模型训练、RAG、Agent 或 Multi-Agent。

## 命令（代码事实）

```powershell
python knowledge_qa_only/KQA_P2_expansion/scripts/build_kqa_v2.py
python knowledge_qa_only/KQA_P2_expansion/validation/test_kqa_v2.py
Get-FileHash knowledge_qa_only/datasets/knowledge_qa_v1_candidates.jsonl -Algorithm SHA256
Get-FileHash knowledge_qa_only/KQA_P2_expansion/datasets/knowledge_qa_v2_candidates.jsonl -Algorithm SHA256
```

结果：`PASS: 33 candidates; 13 reverified + 20 new; traceability, wording, K4/K5 checks passed`。

| 文件 | SHA-256 |
|---|---|
| 冻结 v1（未写回） | `4105757845C9FFD0AA1DD832D0798DEC3877C8E07752CB78878646F0A875D73A` |
| v2 候选集 | `D7B0C1F54385EFF1C6B0812E5EC93D0E5D6871F4B203B22BE557FC19CE11C95A` |

测试是数据结构与规则检查，不等同于独立领域专家审核。
