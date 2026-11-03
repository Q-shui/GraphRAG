"""Assess machine-readable text availability for the three complete local books."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
BOOKS = [
    ROOT / "现代铝电解" / "现代铝电解 -- 刘业翔等著 -- 2008 -- 北京：冶金工业出版社 -- 9787502445768 -- 3244a0affa302decce91ad6f6afd9aee -- Anna’s Archive.pdf",
    ROOT / "铝电解生产技术" / "铝电解生产技术 (杨升，杨冠群编著, 杨昇, 杨冠群编著, 杨昇, 杨冠群) (Z-Library).pdf",
    ROOT / "铝电解技术问答" / "铝电解技术问答 (杨升，杨冠群编著, 杨昇, 杨冠群编著, 杨昇, 杨冠群) (Z-Library).pdf",
]
OUTPUT = ROOT / "aluminum_industry_qa_benchmark" / "sources" / "key_book_text_audit.json"


def main() -> None:
    audit = []
    for book in BOOKS:
        reader = PdfReader(str(book))
        lengths = [len((page.extract_text() or "").strip()) for page in reader.pages]
        audit.append(
            {
                "file": book.name,
                "pages": len(reader.pages),
                "pages_with_nonempty_extractable_text": sum(length > 0 for length in lengths),
                "median_text_chars_per_page": sorted(lengths)[len(lengths) // 2],
                "first_10_page_text_chars": lengths[:10],
                "interpretation": "Nonempty text extraction is only a screening signal. Page-level OCR and visual checks remain necessary before using any passage as evidence.",
            }
        )
    OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
