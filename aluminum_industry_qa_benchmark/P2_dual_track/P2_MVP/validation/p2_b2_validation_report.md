# P2-B2 validation report

- 时间：2026-10-22，Asia/Shanghai 工作会话。
- 冻结检查：知识候选 JSONL SHA-256 为 `5AFE305C47BE0BE0E8DE42EB695F1A5417F931B79C5CF240EAB8307C76E6F88F`；15 条均为 Evidence-Verified，0 条 Expert-Approved；K015 仍带专家审核限制。
- P1 重放：P1 单元测试与独立 verifier 通过 P1Q001–P1Q007 和 2726 回归。
- 新数据题：构建 11 条，JSONL SHA-256 为 `C7AE1E7058BB09A6BDF72BD7BA552D36C8F956D46CB5C79585C1EBAAA5420D58`。
- 工具测试：schema、查询、2726 回归、质量、类型、日期倒置、字段白名单和无记录错误均 PASS；每条 reference tool sequence 被实际执行。
- 独立验证：`independent_verify_data_mvp.py` 对 D009–D018 全部 PASS。该实现仅用 `csv`、`datetime`、`math` 做独立排序、去重、筛选与算术，不导入参考工具或 P1 计算器。
- 边界：D018 为拒答任务，不适用数值独立计算；其结论是“当前冻结快照证据不足”，不是关于现场系统的绝对否定。
