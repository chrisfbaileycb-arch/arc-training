# Aegis-Glimmer-30B-CORTEX-GGUF

CORTEX-protocol fine-tune of [meta-models/Muse-Glimmer-30B](https://huggingface.co/meta-models/Muse-Glimmer-30B) (Apache 2.0),
as llama.cpp Q4_K_M GGUF. Runtime: llama.cpp only — no transformers library.
CORE-SPEC v4.2 in weights: Rule 1 fail-closed, [TRACE] grounding, §S:REPAIR strict JSON emission.

| File | sha256 | Status |
| --- | --- | --- |
| `Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf` | `<FILL: from .sha256 sidecar>` | battery 5/5 (job <JOB_ID>) |

## Training
- Base: meta-models/Muse-Glimmer-30B (bf16 safetensors)
- Recipe: QLoRA r=16, alpha=32, TRL >=1.13, 2 epochs, lr 2e-4 cosine, eff batch 8, bf16/nf4, seq 2048
- Corpus: corpus_v5_muse_cortex_full.jsonl (~470 rows; blocks: converse / fail-closed / registry-QA / grounding / trace / repair / symbol-class / ledger)
- Anti-contamination: battery probe surfaces excluded by gate (grep-verified)
- Jobs: train <ID> · merge-quant <ID> · battery <ID> · publish <ID>
- Merge -> convert_hf_to_gguf (--no-mtp if applicable) -> Q4_K_M -> llama-bench load gate

## Battery (CORE-SPEC v4.2) — protocol/battery_glimmer_cortex.py
| Probe | Result | Receipt |
| converse-normal | <PASS> | <log line> |
| fail-closed-exact | <PASS> | <log line> |
| trace-header | <PASS> | <log line> |
| repair-patch-executable (pytest) | <PASS> | exit=0 |
| budget-closing-syntax | <PASS> | <log line> |

## Capability preservation (owner rule)
20 fixed general prompts, stock vs fine-tuned, same box: <RESULT — no regression beyond noise | REGRESSED: details>

## Usage
- llama.cpp >= b10353 (drive bundles b11382). --jinja --temp 1.0 --top-p 0.95 --top-k 64
- Reasoning model: allow >=800 max tokens.
- Vision (mmproj) and DFlash drafter: use the stock companions from meta-models/Muse-Glimmer-30B-GGUF
  (they pair with this text model; re-derive only if the adapter touched the ViT — it did not).

## Honesty ledger
- Measured: the 5 battery probes above, load gate, speed A/B (<fill>), resident RAM (<fill>).
- UNMEASURED: everything else — general reasoning, multilingual, long-context, tool-call
  reliability beyond the battery, identity behavior (not trained; may still self-ID as base).
- Harness notes: <fill — any fixes the battery or harness required, disclosed>
- Spend ledger: <job costs incl. duplicates>
- Residual nits: <fill — do not polish these out of the record>
