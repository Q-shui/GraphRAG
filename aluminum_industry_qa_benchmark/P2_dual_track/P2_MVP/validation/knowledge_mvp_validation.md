# Knowledge MVP validation record

- 时间：2026-10-22，Asia/Shanghai 工作会话。
- 构建：`python scripts/build_knowledge_mvp.py` 输出 15 条，Evidence-Verified=15，Expert-Approved=0。
- 自动检查：`python tests/test_knowledge_mvp.py` 通过 schema、题号、状态边界、K6、来源多样性、精确重复和答案全文泄漏初筛。
- 候选 JSONL SHA-256：`5AFE305C47BE0BE0E8DE42EB695F1A5417F931B79C5CF240EAB8307C76E6F88F`。
- 审查表：使用 artifact-tool 生成；检查 `审查表!A1:M16`，公式错误搜索命中 0；已渲染预览并人工检查可读性。
- 失败记录：审查表构建首次因 Windows 路径 URL 百分号编码找不到 JSONL；改用 `fileURLToPath` 后重试成功。未修改原始教材或 P0/P1/P2 第一单元文件。
