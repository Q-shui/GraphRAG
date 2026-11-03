# P0 研究日志

| 时间（Asia/Shanghai） | 动作 | 命令/方法 | 结果 |
|---|---|---|---|
| 2026-10-21 | 读取研究任务与协作规则 | 用户提供任务文本；`AGENTS.md` | 仅执行 P0；采用证据审计，停止在阶段报告。 |
| 2026-10-21 | 清点本地资料 | `rg --files`；PowerShell 文件清单 | 发现三套教材、工程 Markdown、数据说明、21 份日报和 3 份 XLSX。 |
| 2026-10-21 | Water-MAS 解读 | `pdfinfo`、PDF 页面渲染、正文检索 | 核验 12 页正文、三 Agent、解耦机制及 260+114 数据集结构。 |
| 2026-10-21 | Water-MAS 可复现性检索 | DOI/题名/GitHub 公开检索 | 未找到可核验代码、题库、工具 schema 或补充材料下载；不等于不存在。 |
| 2026-10-21 | 审计 XLSX | Python 3.12.14 + openpyxl 3.1.5，只读加载 | 生成 `sources/xlsx_structural_audit.json` 与 `sources/model_xlsx_metrics.json`。 |
| 2026-10-21 | 审计旧式 XLS 日报 | Excel COM：`ReadOnly=$true`，不保存 | 生成 `sources/daily_xls_structural_audit.json`；共 21 槽、30,691 行、63 条完全重复。 |
| 2026-10-21 | 检测书籍文本可提取性 | Python 3.12.14 + pypdf | 三本完整扫描书的非空可提取文本页均仅 1 页；后续须 OCR+人工核验。 |
| 2026-10-21 | 输出 P0 报告 | 本目录 Markdown | 完成并停止；未生成题库、训练、Agent 或修改任何原始资料。 |

随机种子：本 P0 未进行随机过程。  
失败/限制：系统 Python 无 pandas；使用捆绑 Python。捆绑 Python 缺少 `xlrd`，故旧式 XLS 改用本机 Excel COM 的只读模式读取。MiKTeX `pdftotext` 因其日志目录权限问题失败，改用 PDF 页面渲染与已可读取的 PDF 正文证据，不影响报告中的页面级人工核验。
