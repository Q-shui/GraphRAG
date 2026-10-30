"""Re-OCR split chapters and build provenance-preserving extraction JSON.

This produces a new corpus and never overwrites the source PDFs, the first OCR
run, or `modern_aluminum_kg_corpus`.  It preserves PSM-3 OCR verbatim, then
creates a separate extraction field that only removes whitespace *between two
CJK characters*.  It does not attempt semantic correction of OCR mistakes.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[0]
UPSTREAM = (WORKSPACE / "aluminum_industry_qa_benchmark" / "knowledge_qa_only" /
            "KQA_P8_textbook_qa")
OCR_ROOT = UPSTREAM / "batches" / "full_textbook_ocr"
SOURCE_MANIFEST = OCR_ROOT / "source_manifest.json"
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = UPSTREAM / "tools" / "tessdata"
OUT_OCR = ROOT / "ocr_psm3"
OUT_CHAPTERS = ROOT / "chapters"
OUT_DATA = ROOT / "data"
FULL_BOOK = WORKSPACE / "现代铝电解" / (
    "现代铝电解 -- 刘业翔等著 -- 2008 -- 北京：冶金工业出版社 -- "
    "9787502445768 -- 3244a0affa302decce91ad6f6afd9aee -- Anna’s Archive.pdf"
)
CHINESE = r"\u4e00-\u9fff"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(WORKSPACE.resolve()).as_posix()


def text_path_for(image_path: Path, chapter_key: str) -> Path:
    return OUT_OCR / chapter_key / f"{image_path.stem}.txt"


def ocr_psm3(image_path: Path, output: Path) -> tuple[Path, str]:
    if output.exists() and output.stat().st_size > 0:
        return output, "existing"
    output.parent.mkdir(parents=True, exist_ok=True)
    base = output.with_suffix("")
    command = [str(TESSERACT), str(image_path), str(base), "-l", "chi_sim",
               "--psm", "3", "--tessdata-dir", str(TESSDATA)]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"OCR failed for {image_path}: {result.stderr[-400:]}")
    return output, "created"


def remove_intra_cjk_spaces(text: str) -> str:
    """A reversible-in-meaning formatting repair, retaining raw OCR separately."""
    previous = None
    result = text
    pattern = re.compile(fr"(?<=[{CHINESE}])[ \t]+(?=[{CHINESE}])")
    while previous != result:
        previous, result = result, pattern.sub("", result)
    return result


def model_text(raw: str) -> str:
    repaired = remove_intra_cjk_spaces(raw)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in repaired.splitlines()]
    return "\n".join(line for line in lines if line)


def quality_flags(raw: str, clean: str) -> list[str]:
    flags: list[str] = []
    if not clean:
        flags.append("empty_ocr")
    elif len(clean) < 80:
        flags.append("short_ocr")
    if "�" in raw or "□" in raw:
        flags.append("replacement_or_unknown_character")
    visible = sum(not char.isspace() for char in raw)
    cjk = sum("\u4e00" <= char <= "\u9fff" for char in raw)
    if visible >= 120 and cjk / visible < 0.35:
        flags.append("complex_layout_formula_table_or_low_cjk_density")
    if re.search(r"(?:[\u4e00-\u9fff][ \t]+){3,}[\u4e00-\u9fff]", raw):
        flags.append("raw_cjk_spacing_repaired_for_model_only")
    return flags


def chunk(text: str, limit: int = 1100, overlap: int = 140) -> list[str]:
    if not text:
        return []
    paragraphs = [x.strip() for x in re.split(r"\n{2,}", text) if x.strip()]
    if len(paragraphs) < 2:
        paragraphs = [x.strip() for x in text.splitlines() if x.strip()]
    result: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        candidate = paragraph if not buffer else buffer + "\n" + paragraph
        if buffer and len(candidate) > limit:
            result.append(buffer)
            buffer = buffer[-overlap:] + "\n" + paragraph
        else:
            buffer = candidate
    if buffer:
        result.append(buffer)
    return result


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    if not TESSERACT.exists() or not TESSDATA.exists() or not FULL_BOOK.exists():
        raise RuntimeError("Required local OCR executable, language data, or complete source PDF is missing")
    OUT_OCR.mkdir(parents=True, exist_ok=True)
    OUT_CHAPTERS.mkdir(parents=True, exist_ok=True)
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    entries = [x for x in json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8")) if x["book_id"] == "B01"]
    all_jobs: list[tuple[Path, Path]] = []
    indexed: list[tuple[int, dict, list[Path], Path, Path]] = []
    for chapter_no, entry in enumerate(entries, 1):
        ocr_dir = UPSTREAM / Path(entry["ocr_dir"].replace("\\", "/"))
        image_dir = UPSTREAM / Path(entry["image_dir"].replace("\\", "/"))
        images = sorted(image_dir.glob("page-*.png"))
        if len(images) != entry["pdf_pages"]:
            raise RuntimeError(f"Unexpected page count: {entry['chapter_file']}")
        key = image_dir.name
        indexed.append((chapter_no, entry, images, image_dir, ocr_dir))
        all_jobs.extend((image, text_path_for(image, key)) for image in images)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for index, (_, state) in enumerate(executor.map(lambda pair: ocr_psm3(*pair), all_jobs), 1):
            if index % 50 == 0:
                print(json.dumps({"ocr_complete": index, "ocr_total": len(all_jobs), "state": state}))

    full_sha = sha256(FULL_BOOK)
    page_records: list[dict] = []
    chunk_records: list[dict] = []
    chapter_index: list[dict] = []
    quality: Counter[str] = Counter()
    ordinal = 0
    for chapter_no, entry, images, image_dir, _ in indexed:
        chapter_id = f"modern_aluminum_v2_chapter_{chapter_no:02d}"
        chapter_pages: list[dict] = []
        for chapter_page, image in enumerate(images, 1):
            ordinal += 1
            text_file = text_path_for(image, image_dir.name)
            raw = text_file.read_text(encoding="utf-8", errors="strict")
            clean = model_text(raw)
            flags = quality_flags(raw, clean)
            quality.update(flags)
            page_id = f"modern_aluminum_v2_{chapter_no:02d}_{chapter_page:03d}"
            record = {
                "record_type": "ocr_page_v2",
                "page_id": page_id,
                "book_id": "modern_aluminum_2008",
                "book_title": "现代铝电解",
                "chapter_id": chapter_id,
                "chapter_file": entry["chapter_file"],
                "chapter_page": chapter_page,
                "book_page_ordinal_in_split_collection": ordinal,
                "source_complete_book_pdf": rel(FULL_BOOK),
                "source_complete_book_pdf_sha256": full_sha,
                "source_chapter_pdf": f"现代铝电解/{entry['chapter_file']}",
                "source_chapter_pdf_sha256": entry["source_sha256"].lower(),
                "source_image": rel(image),
                "source_image_sha256": sha256(image),
                "ocr_psm3_file": rel(text_file),
                "ocr_psm3_file_sha256": sha256(text_file),
                "ocr_text_verbatim": raw,
                "text_for_extraction": clean,
                "normalization": {
                    "operation": "remove spaces/tabs only when flanked by two CJK characters; trim line whitespace",
                    "semantic_correction": "none",
                    "raw_ocr_preserved": True,
                },
                "ocr_engine": "Tesseract 5.4.0 chi_sim",
                "page_segmentation_mode": 3,
                "ocr_confidence": None,
                "quality_flags": flags,
                "review_status": "unreviewed",
                "graph_ingestion_status": "candidate_only",
                "use_constraint": "Any extracted claim must cite this page and be checked against source_image before acceptance.",
            }
            chapter_pages.append(record)
            page_records.append(record)
            for chunk_no, content in enumerate(chunk(clean), 1):
                chunk_records.append({
                    "record_type": "extraction_chunk_v2",
                    "chunk_id": f"{page_id}_c{chunk_no:02d}",
                    "page_id": page_id,
                    "chapter_id": chapter_id,
                    "chapter_file": entry["chapter_file"],
                    "book_page_ordinal_in_split_collection": ordinal,
                    "text": content,
                    "source_image": rel(image),
                    "review_status": "unreviewed",
                    "graph_ingestion_status": "candidate_only",
                })
        chapter_doc = {
            "record_type": "chapter_ocr_corpus_v2",
            "book_id": "modern_aluminum_2008",
            "book_title": "现代铝电解",
            "chapter_id": chapter_id,
            "chapter_order": chapter_no,
            "chapter_file": entry["chapter_file"],
            "source_chapter_pdf": f"现代铝电解/{entry['chapter_file']}",
            "source_chapter_pdf_sha256": entry["source_sha256"].lower(),
            "source_pdf_pages": entry["pdf_pages"],
            "pages": chapter_pages,
            "page_count": len(chapter_pages),
            "review_status": "unreviewed",
            "coverage_note": "This is the 616-page split-chapter collection. The complete source PDF has 650 pages; its 34-page difference is not yet mapped.",
        }
        (OUT_CHAPTERS / f"modern_aluminum_v2_chapter_{chapter_no:02d}.json").write_text(
            json.dumps(chapter_doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        chapter_index.append({"chapter_id": chapter_id, "chapter_order": chapter_no, "chapter_file": entry["chapter_file"], "pages": len(chapter_pages)})
    write_jsonl(OUT_DATA / "modern_aluminum_v2_pages.jsonl", page_records)
    write_jsonl(OUT_DATA / "modern_aluminum_v2_extraction_chunks.jsonl", chunk_records)
    write_jsonl(OUT_DATA / "modern_aluminum_v2_chapters.jsonl", chapter_index)
    manifest = {
        "artifact": "modern_aluminum_kg_corpus_v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_command": "python modern_aluminum_kg_corpus_v2/scripts/build_chapter_ocr_v2.py",
        "source": "existing 250-DPI local chapter renders; re-OCR with Tesseract PSM 3",
        "chapters": len(chapter_index), "pages": len(page_records), "chunks": len(chunk_records),
        "quality_flag_counts": dict(sorted(quality.items())),
        "python_version": sys.version, "platform": platform.platform(), "random_seed": None,
        "limitations": [
            "OCR is not a semantic correction or expert verification.",
            "Tables, figures, formulas, and numeric thresholds require image-level review.",
            "The 34-page coverage difference between split chapters and complete PDF remains unresolved.",
        ],
    }
    (ROOT / "build_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"chapters": len(chapter_index), "pages": len(page_records), "chunks": len(chunk_records), "quality_flags": dict(quality)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
