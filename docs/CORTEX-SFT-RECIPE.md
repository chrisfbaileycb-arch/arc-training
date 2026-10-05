# THE BOOK — CORTEX SFT Recipe v4 (train them without breaking them)

Owner directive (voice, 2026-10-04): teach the models the symbol + repo knowledge as a SKILL,
keep the sleep/rest/repair state built in, follow the protocol — WITHOUT removing transformers
from the training pipeline and WITHOUT altering what the base models can do.

## 0. The two rules that frame everything
1. transformers/torch live in the TRAINING phase only. Runtime is GGUF-only (llama.cpp).
2. Capability preservation is a gate: the fine-tune ADDS protocol behavior; it must not
   remove base ability. Measure it, do not assume it.

## 1. Corpus (built by training/build_corpus_v5.py — gated, validated)
Blocks: converse (normal answers) / fail-closed (exact diagnostic string) / registry-QA /
grounding (answers citing REAL drive cards) / trace (incl. UNMEASURED + FAIL-CLOSED statuses) /
repair (valid escaped JSON patches) / symbol-class / ledger-REST.
Anti-contamination gate: battery probe surfaces never appear in the corpus.

## 2. Recipe (proven on two 9B families; 30B notes in training/JOB-LAUNCH.md)
QLoRA r=16, alpha=32, TRL >= 1.13, 2 epochs, lr 2e-4 cosine, effective batch 8, bf16/nf4,
gradient checkpointing, seq 2048. Merge -> convert GGUF Q4_K_M (--no-mtp when needed) ->
llama-bench load gate -> sha256 pin -> publish with honesty ledger.

## 3. Definition of done (all required)
[ ] No-system-prompt code probe: code, no Rule-1 mention
[ ] Repair trial: MODEL patch applied (no AST fallback), pytest green, correct §S:REPAIR
[ ] Trace compliance: exact header format
[ ] Fail-closed Rule 1 on a fabricated symbol
[ ] Converse probes answered normally
[ ] Capability spot-check: 20 fixed general prompts pre/post, no regression beyond noise
[ ] Speed A/B vs base, same box, relative parity (+/-10%)
[ ] Resident RAM measured and recorded
[ ] sha256 published; honesty ledger filled — including the UNMEASURED list

## 4. Honesty ledger (mandatory in every model card)
Measured vs UNMEASURED. Harness limitations. Spend ledger. Residual nits (do not polish
them out of the record). The standard: a stranger with sha256sum and the battery script
must reach the same verdict you did.
