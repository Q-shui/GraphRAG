# 《现代铝电解》V2 OCR 图谱语料

本目录是独立于 `modern_aluminum_kg_corpus` 的改进版，不覆盖任何原教材、页图或 V1 OCR。

每章 JSON 保留 `ocr_text_verbatim`，并另外提供仅修复中文字符间空白的 `text_for_extraction`。该规范化不是人工校勘；所有候选知识必须回查 `source_image` 后才可进入正式图谱。

`data/modern_aluminum_v2_extraction_chunks.jsonl` 是给本地模型逐块抽取的输入。模型输出必须标为 `candidate_only`，并保留 `page_id` 和原文短引。
