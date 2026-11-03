# Dataset Card

- 任务：教材来源的电解铝专业知识问答。
- 当前候选题数：16；其中 `TEXTBOOK_VERIFIED=3`、`NEEDS_PAGE_REVIEW=10`、`INFERENCE_REVIEW_REQUIRED=3`。
- 被拒绝草题：16；均与KQA-P7第003批语义重复。
- 证据状态：未将章节标题或既有工程经验切片冒充为新页级教材证据。
- 专家审核：未开展，均不得标记为 Expert-Approved。
- 使用限制：只能将3条已页核验题用于教材候选集的人工审阅；整批尚不可作为正式模型评测集或性能结论。

## 统一候选池

`datasets/unified_candidate_pool.jsonl` 共有168条候选题，达到P8长期目标的最低数量门槛（150）。它是历史候选集与本批题目的可追溯汇总，不是专家批准、也不是已经分割并冻结的正式Benchmark。

统一池的168条题目均已带有 `reference_answer`。其中P4、P6和P7的答案来自其原有、按相同 `question_id` 关联的 `answers.jsonl`；P5、P5.1和P8的答案原本随题目记录保存。此为字段完整性修复，不改写任何历史参考答案。
