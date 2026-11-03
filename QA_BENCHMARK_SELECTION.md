# Aluminum QA selection for graph-RAG experiments

## Recommendation

Take out `knowledge_qa_only/KQA_P8_textbook_qa/datasets/unified_candidate_pool.jsonl`
as the **168-question exploratory candidate pool**, not as a frozen benchmark.
It is the only observed 168-record version and every record has a reference
answer, so it is useful for exercising the batch-QA interface, coverage and
error analysis after graph construction.

Do **not** use its aggregate answer score as a paper-quality final claim: all
168 are `Not-Reviewed`; 121 have `HISTORICAL_STATUS_UNMAPPED`; only 3 have
`TEXTBOOK_VERIFIED`; 59 have no source IDs and the majority derive from a
different evidence/source lineage than `modern_aluminum_kg_corpus_v2`.

For a defensible first textbook-aligned evaluation slice, use
`knowledge_qa_only/KQA_P2_expansion/datasets/knowledge_qa_benchmark_view.jsonl`
(33 questions).  Its records contain page-level evidence excerpts and
`Evidence-Verified` status, although they too remain expert-unreviewed and
must be mapped from their legacy `MODxx` source designation to V2 page/chunk
IDs before evidence-retrieval metrics are reported.

`KQA_P8_textbook_qa/datasets/textbook_benchmark_view.jsonl` has only 3
page-verified questions, so it is a smoke-test set, not sufficient by itself.

## Required protocol

1. Keep the 168 records outside training/prompt-tuning; label outputs
   exploratory.
2. Create an immutable derived split with a manifest and record source/prompt/
   graph version. Do not overwrite the benchmark source.
3. Report answer score only on an independently reviewed frozen subset.
4. For graph comparisons, report evidence retrieval separately and exclude a
   question if its source page cannot be mapped to current V2 provenance.
