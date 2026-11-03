"""Compute reproducible, read-only quality metrics for the three XLSX sources."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.utils.datetime import from_excel


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "2020YFB1713603-001-电解铝跨工序能质耦合、工艺参数感知模型数据集" / "数据集实体文件"
OUTPUT = ROOT / "aluminum_industry_qa_benchmark" / "sources" / "model_xlsx_metrics.json"


def serialize(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def rows_after_header(ws: object, header_row: int) -> list[tuple[object, ...]]:
    return list(ws.iter_rows(min_row=header_row + 1, values_only=True))


def metric_for_sheet(ws: object, header_row: int) -> dict[str, object]:
    rows = rows_after_header(ws, header_row)
    width = ws.max_column
    missing = [sum(row[col] is None for row in rows) for col in range(width)]
    duplicates = sum(count - 1 for count in Counter(rows).values() if count > 1)
    return {
        "sheet": ws.title,
        "header_row": header_row,
        "headers": [serialize(cell.value) for cell in ws[header_row]],
        "data_rows": len(rows),
        "exact_duplicate_rows": duplicates,
        "missing_by_column": missing,
    }


def main() -> None:
    output: dict[str, object] = {}
    temperature = openpyxl.load_workbook(SOURCE / "工艺参数感知模型数据.xlsx", read_only=True, data_only=True)
    ws = temperature.active
    temperature_metric = metric_for_sheet(ws, 1)
    rows = rows_after_header(ws, 1)
    excel_dates = [row[1] for row in rows if isinstance(row[1], (int, float))]
    temperature_metric["excel_date_min"] = min(excel_dates)
    temperature_metric["excel_date_max"] = max(excel_dates)
    temperature_metric["date_min"] = from_excel(min(excel_dates)).date().isoformat()
    temperature_metric["date_max"] = from_excel(max(excel_dates)).date().isoformat()
    temperature_metric["distinct_cell_ids"] = sorted({row[0] for row in rows if row[0] is not None})
    output["工艺参数感知模型数据.xlsx"] = temperature_metric
    temperature.close()

    bake = openpyxl.load_workbook(SOURCE / "焙烧控制模型数据.xlsx", read_only=True, data_only=True)
    ws = bake.active
    bake_metric = metric_for_sheet(ws, 2)
    rows = rows_after_header(ws, 2)
    minute_values = [row[0] for row in rows if isinstance(row[0], (int, float))]
    bake_metric["minute_min"] = min(minute_values)
    bake_metric["minute_max"] = max(minute_values)
    bake_metric["distinct_minutes"] = len(set(minute_values))
    bake_metric["missing_minutes_between_min_and_max"] = int(max(minute_values) - min(minute_values) + 1 - len(set(minute_values)))
    output["焙烧控制模型数据.xlsx"] = bake_metric
    bake.close()

    tap = openpyxl.load_workbook(SOURCE / "出铝量预测模型数据.xlsx", read_only=True, data_only=True)
    output["出铝量预测模型数据.xlsx"] = {
        "sheet1": metric_for_sheet(tap["Sheet1"], 2),
        "sheet2_parameter_table": metric_for_sheet(tap["Sheet2"], 2),
        "sheet3": metric_for_sheet(tap["Sheet3"], 2),
        "interpretation_boundary": "Sheet1 includes model output labels and Sheet3 has numeric ordinal headings; neither is treated as raw, time-indexed observation without external metadata.",
    }
    tap.close()
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
