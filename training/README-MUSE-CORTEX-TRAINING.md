# Aegis-Glimmer-30B-CORTEX — weights-layer training kit (CORE-SPEC v4.2)

Two layers install this protocol. Be precise about which is which:

| layer | what | status |
|---|---|---|
| runtime injection | `protocol/glimmer_cortex_system_prompt.txt` applied as system prompt by launchers/UI/Hey Buddy | DONE — works today on the stock GGUF |
| in-weights training | QLoRA on `meta-models/Muse-Glimmer-30B` teaching this exact spec | THIS KIT — you run the job |

## Corpus
`training/corpus_v5_muse_cortex_seed.jsonl` — 24 owner-reviewed seed examples:
4 converse (normal answers, no protocol), 4 fail-closed (exact diagnostic string),
4 [TRACE] (incl. UNMEASURED and FAIL-CLOSED statuses), 3 §S:REPAIR (valid JSON,
properly escaped diffs — the v2 quote-bug is dead here), 2 symbol-class, 2 ledger/REST.
Extend to the v4-recipe shape (~450-500 rows) by scaling each block proportionally and
adding grounding rows generated from your own `symbols/schemas` cards.
FINAL CORPUS RULE: embed `protocol/cortex_system_directive.md` verbatim as the system
message in every row (the seed uses a condensed system for readability).

Anti-contamination gate: grep the final corpus for every probe string in
`protocol/battery_glimmer_cortex.py` (`quantum_flux_capacitor`, the calc fixture,
`adds two numbers`, etc.). A match = reject. The battery must remain a transfer test.

## Recipe (your proven one, scaled to 30B)
QLoRA r=16, alpha=32, TRL >= 1.13, 2 epochs, lr 2e-4 cosine, eff batch 8, bf16/nf4,
gradient checkpointing, seq 2048. 30B on 24 GB is tight-but-runnable; 48 GB comfortable.
Merge -> convert Q4_K_M (watch mtp metadata; `--no-mtp` if conversion emits it) ->
llama-bench load gate -> sha256 pin -> publish with honesty ledger.

## Definition of done
`python protocol/battery_glimmer_cortex.py --base http://127.0.0.1:8080`
must exit 0 (6/6 probes, including the no-system-prompt code probe) against the FINE-TUNED model,
then the stock model for the A/B ledger. Publish: model card with sha256, battery receipts,
UNMEASURED list, spend ledger.

## Capability preservation (owner rule: do not alter the models)
Score 20 fixed general prompts (explanation, code, reasoning) pre/post fine-tune;
no regression beyond noise, or the run does not ship.
