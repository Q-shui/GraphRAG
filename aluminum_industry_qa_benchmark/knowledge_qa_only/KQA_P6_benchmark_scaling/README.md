# KQA-P6 规模化构建主账本

本目录不覆盖 P4–P5.2。`BUILD_STATE.json` 是断点续建入口；`batch_001` 是首个追加式批次。候选题、Review-Ready 与 Gold 严格区分：本轮没有 Gold 项，也没有真实专家审核结果。

运行：`python scripts/build_batch_001.py`，随后 `python scripts/validate_batch_001.py`。
