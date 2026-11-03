"""Read-only structural audit for the supplied XLSX source data.

The script deliberately does not write to, rename, or recalculate any source
workbook.  It outputs a compact JSON report with sheet dimensions, sample
rows, and cell-level missingness for later evidence review.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import openpyxl


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "2020YFB1713603-001-电解铝跨工序能质耦合、工艺参数感知模型数据集" / "数据集实体文件"
OUTPUT = ROOT / "aluminum_industry_qa_benchmark" / "sources" / "xlsx_structural_audit.json"


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def audit_sheet(ws: Any) -> dict[str, Any]:
    rows = list(ws.iter_rows(values_only=True))
    width = ws.max_column
    missing_by_column = [0] * width
    nonempty_by_column = [0] * width
    for row in rows:
        for index, value in enumerate(row):
            if value is None:
                missing_by_column[index] += 1
            else:
                nonempty_by_column[index] += 1
    return {
        "sheet": ws.title,
        "rows_reported_by_openpyxl": ws.max_row,
        "columns_reported_by_openpyxl": width,
        "first_five_rows": [[to_jsonable(value) for value in row] for row in rows[:5]],
        "missing_cells_by_column_index": missing_by_column,
        "nonempty_cells_by_column_index": nonempty_by_column,
    }


def main() -> None:
    report: dict[str, Any] = {"source_dir": str(SOURCE_DIR), "workbooks": []}
    for path in sorted(SOURCE_DIR.glob("*.xlsx")):
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        report["workbooks"].append(
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "sheets": [audit_sheet(workbook[name]) for name in workbook.sheetnames],
            }
        )
        workbook.close()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
