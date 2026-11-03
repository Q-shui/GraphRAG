"""Independent commands for the modern-aluminum candidate KG experiment.

Examples:
  python modern_aluminum.py audit --corpus modern_aluminum_kg_corpus_v2 --output runs/audit.json
  python modern_aluminum.py build --corpus modern_aluminum_kg_corpus_v2 --config Option/Config2.yaml --output runs/pilot --limit 2
"""
from __future__ import annotations

import argparse
import asyncio
import json
import hashlib
from pathlib import Path

from Data.ModernAluminumDataset import ModernAluminumDataset
from Data.AluminumQADataset import AluminumQADataset


def write_report(path: str | Path, data: dict) -> None:
    destination = Path(path); destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


async def build(args) -> None:
    # Keep the read-only audit command usable in a minimal Python environment.
    from Core.AluminumKG.CandidatePipeline import CandidateExtractor, export_candidate_graph, load_checkpoint
    from Core.Provider.LLMProviderRegister import create_llm_instance
    from Option.Config2 import Config
    dataset = ModernAluminumDataset(args.corpus)
    if not args.all and args.limit is None:
        raise SystemExit("Specify --limit for a pilot or --all for an explicit full-corpus server run.")
    chunks = list(dataset.iter_chunks(chapters=args.chapter, ids=args.chunk_id, review_status=args.review_status, limit=args.limit))
    if not chunks:
        raise SystemExit("No valid chunks selected; inspect audit output and filters.")
    # Config.parse retains the repository's established native Ollama adapter.
    config = Config.parse(Path(args.config), dataset_name="modern_aluminum_candidate")
    llm = create_llm_instance(config.llm)
    run_identity = {"corpus": str(Path(args.corpus).resolve()), "llm_model": config.llm.model,
                    "temperature": config.llm.temperature, "seed": config.llm.seed, "context": config.llm.ollama_num_ctx,
                    "prompt_version": "modern-aluminum-candidate-v1", "schema": "candidate-occurrence-v1"}
    fingerprint = hashlib.sha256(json.dumps(run_identity, sort_keys=True).encode()).hexdigest()
    output = Path(args.output); identity_path = output / "run_identity.json"
    if args.resume and identity_path.exists():
        prior = json.loads(identity_path.read_text(encoding="utf-8"))
        if prior.get("fingerprint") != fingerprint:
            raise SystemExit("Refusing resume: corpus/model/prompt/schema fingerprint changed. Use a new output directory.")
    elif args.resume and (output / "candidate_extractions.jsonl").exists():
        raise SystemExit("Refusing resume without run_identity.json; use a new output directory.")
    cached = load_checkpoint(output / "candidate_extractions.jsonl") if args.resume else {}
    extractor = CandidateExtractor(llm)
    results = [cached[chunk.chunk_id] for chunk in chunks if chunk.chunk_id in cached]
    pending = [chunk for chunk in chunks if chunk.chunk_id not in cached]
    for number, chunk in enumerate(pending, 1):
        results.append(await extractor.extract(chunk))
        # Atomic enough for JSONL recovery: each completed chunk becomes a
        # checkpoint before the next expensive local inference begins.
        export_candidate_graph(results, output)
        print(f"completed={number}/{len(pending)} cached={len(cached)} chunk_id={chunk.chunk_id}")
    counts = export_candidate_graph(results, args.output)
    manifest = {"corpus": str(Path(args.corpus).resolve()), "selection": {"chapters": args.chapter, "chunk_ids": args.chunk_id,
                "review_status": args.review_status, "limit": args.limit}, "llm": {"api_type": str(config.llm.api_type.value),
                "model": config.llm.model, "ollama_host": config.llm.ollama_host, "temperature": config.llm.temperature,
                "seed": config.llm.seed, "context": config.llm.ollama_num_ctx}, "counts": counts,
                "fingerprint": fingerprint, "reused_chunks": len(cached), "new_chunks": len(pending)}
    write_report(Path(args.output) / "run_manifest.json", manifest)
    write_report(identity_path, {"fingerprint": fingerprint, **run_identity})
    print(json.dumps(counts, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Modern aluminum candidate KG workflow")
    subs = parser.add_subparsers(dest="command", required=True)
    audit = subs.add_parser("audit", help="Read-only corpus audit")
    audit.add_argument("--corpus", required=True)
    audit.add_argument("--output", required=True)
    build_parser = subs.add_parser("build", help="Small, explicit candidate extraction run")
    build_parser.add_argument("--corpus", required=True)
    build_parser.add_argument("--config", required=True)
    build_parser.add_argument("--output", required=True)
    build_parser.add_argument("--limit", type=int, help="Pilot cap; mutually exclusive in intent with --all")
    build_parser.add_argument("--all", action="store_true", help="Explicitly permit all selected corpus chunks")
    build_parser.add_argument("--resume", action="store_true", help="Reuse completed chunks only when run identity matches")
    build_parser.add_argument("--chapter", action="append")
    build_parser.add_argument("--chunk-id", action="append")
    build_parser.add_argument("--review-status", action="append", default=["unreviewed"])
    qa = subs.add_parser("qa-audit", help="Audit external QA JSONL without treating it as gold")
    qa.add_argument("--qa", required=True)
    qa.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.command == "audit":
        report = ModernAluminumDataset(args.corpus).audit()
        write_report(args.output, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.command == "qa-audit":
        dataset = AluminumQADataset(args.qa)
        write_report(args.output, dataset.audit())
        print(json.dumps(dataset.audit(), ensure_ascii=False, indent=2))
    else:
        asyncio.run(build(args))


if __name__ == "__main__":
    main()
