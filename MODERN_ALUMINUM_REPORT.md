# Modern aluminum candidate-KG adaptation report

## Audited execution path

`main.py` currently loads `Data/QueryDataset.RAGQueryDataset`, which requires
`Corpus.json` and `Question.json`; it inserts the corpus and then always runs
QA and evaluation.  `DocChunk.build_chunks` hashes text-derived IDs and
re-chunks all documents.  `ERGraph` performs generic NER then generic OpenIE
and `BaseGraph` merges graph nodes and edges by their string identifiers.
`NetworkXStorage` persists a NetworkX graph, but its node/edge schemas do not
retain page-level evidence occurrences independently.  Therefore candidate
extraction is implemented beside, rather than silently inside, the generic
merged ER graph.

The existing native Ollama adapter is retained: `OllamaLLM` calls `/api/chat`,
`NativeOllamaEmbedding` calls `/api/embed`, both accept no API key and validate
host, JSON responses, retries, timeout, concurrency and embedding dimensions.

## Corpus audit (2026-11-02)

The read-only adapter counted 1,110 valid extraction records, no invalid JSON
or missing required extraction fields, no duplicate `chunk_id`, and no exact
duplicate extraction text groups.  Character lengths range from 98 to 1,100
(902,674 total).  All chunk page IDs map to the 616 page records and the chunks
cover 39 chapters.  None of the 1,110 `source_image` paths resolve relative to
the current corpus directory: these paths point to an upstream image tree that
is not present here, so image-level review is presently blocked but its source
reference is preserved.  This is consistent with the manifest's 39 chapters, 616
pages and 1,110 chunks; the manifest also declares 48 complex-layout risk
pages, 2 empty OCR pages and an unresolved 34-page coverage difference.

## Implemented scope

* `Data/ModernAluminumDataset.py`: read-only deterministic JSONL loader;
  separately represents document, chunk, page and chapter identities.
* `TextChunk.metadata` and `DocChunk` prechunked mode: preserves source IDs and
  metadata, never hashes/re-splits supplied extraction chunks.
* `Core/AluminumKG/CandidatePipeline.py`: Chinese controlled ontology prompt,
  structured response validation, candidate-only status, occurrence-level
  evidence and review/export files.
* `modern_aluminum.py`: separate `audit` and capped `build` commands; build
  never requires questions and refuses an uncapped extraction run.
* `main.py`: preserves the repository's standard method entrypoint for the
  modern corpus.  It auto-selects the prechunked loader and root-level
  `unified_candidate_pool.jsonl`; graph/index/results are written under
  `outputs/modern_aluminum_kg_corpus_v2/` instead of the OCR source directory.
* `tests/test_modern_aluminum.py`: loader, identity, evidence and persistence
  coverage (persistence test runs when project dependencies are installed).

## Method compatibility

| Method/config | Status | Notes |
|---|---|---|
| ER graph / LightRAG / LGraphRAG / GGraphRAG | Partially supported | Shared entity-relation core can consume preserved chunks; their generic prompts and merged graph do not yet expose candidate occurrence exports. |
| HippoRAG | Untested | ER evidence source IDs survive, but PPR/index integration has not been tested. |
| RAPTOR | Untested | Uses summary tree rather than ER facts; needs provenance propagation through summaries. |
| KGP | Untested | Uses passage graph and should use prechunked input, but needs a dedicated integration test. |
| MedG | Not recommended/untested | One-step, regex-formatted medical extraction is not suitable for the structured Chinese candidate schema. |

"Supported" here means code-path compatibility, not successful local-model
experimentation.  No full corpus extraction or QA metric has been claimed.

## Before a full run

1. Activate the project environment and verify `pyyaml`, `scipy`, `loguru`,
   `aiohttp`, `pydantic`, `llama-index`, `tiktoken` and graph dependencies.
2. Verify local `/api/tags`, selected chat model and embedding model; do not
   download models automatically.
3. Pilot on 1--2 chapters, manually inspect OCR/image evidence and tune the
   ontology/prompt before any full construction.
4. Create independently reviewed QA and fact samples before reporting factual,
   graph-quality or answer-quality metrics.
5. Use a unique output directory per corpus hash, model, prompt version,
   generation parameters and code commit.
