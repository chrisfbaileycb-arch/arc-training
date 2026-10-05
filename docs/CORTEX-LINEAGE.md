# CORTEX lineage: from base model to the file on the drive

Everything below the "Cards say" lines comes from the published Hugging Face model cards, copied in
by the owner. It was **not** independently re-measured here. "Verified here" marks the few things this
repo checked itself.

## The chain

```
base model  ->  QLoRA adapter (CORE-SPEC v4.2 corpus)  ->  merged  ->  GGUF Q4_K_M  ->  this drive
```

| core | base | adapter | GGUF (sha256 pinned in `models/cores.json`) |
|---|---|---|---|
| `ornith-9b-cortex` | `ornith-ai/Ornith-1.5-9B` (MIT) | `Johnny5b/Ornith-9B-CORTEX-LoRA-v3` | `Ornith-9B-CORTEX-v3-Q4_K_M.gguf`, 5.63 GB, `ca2803a2...7b93` |
| `mimo-9b-cortex` | `XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B` (MIT) | `Johnny5b/MiMo-9B-CORTEX-LoRA-v1-1` (v1 adapter: `MiMo-9B-CORTEX-LoRA-v1`) | `MiMo-9B-CORTEX-v1.1-Q4_K_M.gguf`, ~5.7 GB, `ec4cb3fb...7036` |
| `muse-glimmer-30b` | `meta-models/Muse-Glimmer-30B` | none yet. The protocol is injected at runtime | hash not pinned yet (`state: pinned`, `sha256: null`) |
| `muse-glimmer-30b-cortex` | Muse-Glimmer-30B | planned, job kit in `training/` | `state: planned` |

Training recipe (cards say): QLoRA r=16, alpha=32, TRL 1.13, 2 epochs, lr 2e-4 cosine, effective batch 8,
bf16/nf4. Ornith v3 trained on the 404-row v3 corpus (final train loss 0.434). MiMo v1.1 added 31
converse rows after v1 refused ordinary requests ("I can't violate rule number one").
Corpus: `Johnny5b/cortex-sft-300`. Other repos named in the cards: `portable-ai-runner`
(build plan), `cortex-knowledge-vault` (harness patcher).

Both 9B GGUFs share the `qwen35` hybrid architecture (32 layers, 427 tensors). Both card hashes match
the pins in `models/cores.json`. (Verified here: the hash strings are identical. The files
themselves are checked on your machine with `scripts/verify_weights.py`.)

## Runtime notes that bite

- **Thinking is on by default.** The chat template ends in `<think>` unless a request sets
  `enable_thinking=false`. Give reasoning cores **800+ tokens**. At 300 the reply is eaten by
  thinking (cards: measured three times). The battery defaults to `--budget 800`.
- **`--jinja` is on by default** in the bundled llama.cpp b11382 (verified here via `llama-server --help`).
- **`llama-server` has no `--stop` flag** in b11382 (verified here). The GGUF's EOS is already `<|im_end|>`
  (id 248046). If you want a stop guard, send `"stop": ["<|im_end|>"]` per request. The battery does.
- **Conversion:** converted with `--no-mtp`. Without it the base config's `mtp_num_hidden_layers`
  produces GGUFs that fail to load.
- Residual `<think></think>` markers may prefix answers at low temperature (card: harmless).

## Patch format

The corpus teaches `{"action": "patch", "target_file", "symbol", "diff"}` where `diff` is a JSON string
`{"find": ..., "replace": ...}`. The upstream trial prints that inner object. The battery accepts either
shape, and **applies** the patch before running pytest. It does not just look for the fix in the text.

## What the cards say they measured (and did not)

- Ornith v3: repair trial passed with the model's own patch, no AST fallback, pytest 3/3. Needed two
  harness fixes (generation cap 300 to 800, last-line patch extractor).
- MiMo v1.1: no-system-prompt code probe, repair trial, trace compliance, Rule 1 fail-closed and converse
  probes all passed. Resident RAM 8.8-9.1 GB.
- **Unmeasured / known wrong, per the cards:** identity (Ornith may say "Qwen", MiMo says "AURA-9"),
  absolute GPU speed for Ornith v3, anything beyond the battery. CPU tokens/sec varied up to 6x
  between runs on shared hosts and is not comparable across runs.
- **Not yet run in this repo:** the six-probe battery in `protocol/` against the real weights. The tests
  here grade the battery's logic against a fake endpoint only.

## Check your copy

```
python scripts/verify_weights.py            # OK / MISMATCH / MISSING / UNPINNED per core
python scripts/verify_weights.py --pin      # record sha256 for cores that have none (Muse)
python protocol/battery_glimmer_cortex.py --base http://127.0.0.1:8080
```
