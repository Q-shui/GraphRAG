# Batch 001 Manifest

- 执行日期：2026-10-22（Asia/Shanghai）。
- 输入：`现代铝电解/29 电解铝厂的烟气净化与环境保护.pdf`，PDF页1–8，对应印刷页457–464。
- 渲染：Poppler `pdftoppm`，250 dpi，PNG保存在 `batches/batch_001/images/`。
- OCR：Tesseract 5.4.0.20240606，官方 `chi_sim` 语言模型 SHA-256 `4FEF2D1306C8E87616D4D3E4C6C67FAF5D44BE3342290CF8F2F0F6E3AA7E735B`。
- 人工页面复核：印刷页457；其余页面仅保存OCR，未提升为页面已核验。
- 输出：16条新候选题，3条 `TEXTBOOK_VERIFIED`，10条 `NEEDS_PAGE_REVIEW`，3条 `INFERENCE_REVIEW_REQUIRED`；16条历史重复草题拒绝。
