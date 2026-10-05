# AEGIS Drive — ARC Training

**An offline, symbolic-AI USB workstation** — GGUF-only inference, a physical on-disk knowledge vault with directional symbol graphs, a three-state lifecycle engine (AWAKE / SELF-REPAIR / REST), a pyggi-style self-repair loop, and the complete training kits that put the CORTEX protocol into model weights. It carries its own llama.cpp runtime for Windows and Linux: **nothing to install on the target machine.**

Built by Chris (Signal F Holdings) with Kernel (Lobe AI). Battery at build time: **24 passed, 1 skipped** — and the skip is the honest kind (it needs a `.gguf` present, not a fabricated pass).

---

## Why this exists

Most "AI builds" are stories. This one is a machine with a lie detector bolted on:

- **Physical knowledge only.** A symbol resolves to a drive-relative file plus its SHA-256 — never a URL, never a placeholder, never a stub.
- **Verification-first.** Completion means raw artifacts: file trees with byte counts, SHA-256 manifests, raw pytest stdout. Narrative summaries are not evidence.
- **Planned means planned.** A model core that has not been trained says `state: planned, sha256: null`. Nobody ships vapor here.
- **Zero transformers at runtime.** transformers/torch live in the *training* phase only. Runtime is llama.cpp / wllama — compiled C++/WASM.
- **Air-gapped execution.** Zero outbound calls from the runtime. The only online-adjacent behavior is a printed health-referral notice telling the *human* to verify current guidance — the system itself never dials out.

---

## The cores (`models/cores.json`)

| core | model file | size | tier | CORTEX protocol |
|---|---|---|---|---|
| `ornith-9b-cortex` | Ornith-9B-CORTEX-v3-Q4_K_M.gguf | 5.63 GB | anywhere (8–16 GB) | **in weights** (v3, battery-verified upstream) |
| `mimo-9b-cortex` | MiMo-9B-CORTEX-v1.1-Q4_K_M.gguf | ~5.7 GB | anywhere | **in weights** (v1.1, battery-verified upstream) |
| `muse-glimmer-30b` | Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf | 16.8 GB | strong host (24 GB+) | CORE-SPEC v4.2 **runtime-injected** |
| `muse-glimmer-30b-cortex` | Aegis-Glimmer-30B-CORTEX-v1-Q4_K_M.gguf | ~16.8 GB | strong host | **PLANNED** — job kit ready in `training/` |

Both 9B CORTEX cores are **pre-pinned to the SHA-256 published in their Hugging Face model cards**; `download_models.py` verifies on receipt and *refuses* mismatches. The 30B-CORTEX core becomes real only when the training job publishes a hash — see below.

---

## Quickstart

```bash
# one-time, with internet — downloads and hash-verifies the weights
python download_models.py --core ornith-9b-cortex
python download_models.py --core mimo-9b-cortex                          # optional
python download_models.py --core muse-glimmer-30b --with-companions      # 24 GB+ hosts

# anywhere, offline — llama.cpp is bundled in runtime/
./serve-model.sh ornith-9b-cortex        # Linux   -> http://127.0.0.1:8080
serve-model.bat                          # Windows (defaults to ornith-9b-cortex)

# drive UI in the browser (wllama, weights stream from the drive)
python serve.py                          # then open http://127.0.0.1:8080 -> Load model

# the battery
python -m pytest tests/ -v
```

**The offline proof:** turn Wi-Fi off, ask for a function, watch tokens generate. Then `sha256sum` the model file against the pinned hash in `models/cores.json`. Match = authentic, untampered, yours.

---

## The 30B CORTEX job (`training/`)

Everything needed to produce **Aegis-Glimmer-30B-CORTEX** (CORE-SPEC v4.2 in weights) on one HF Job:

| file | role |
|---|---|
| `build_corpus_v5.py` + `expand_corpus_v5.py` | build the **781-row gated corpus** — 596 grounding rows generated from real extraction cards; anti-contamination, repair-JSON, and fail-closed gates enforced |
| `train_qlora.py` | QLoRA r=16 / α=32 / TRL / 2 epochs / lr 2e-4 cosine / bf16-nf4 — the recipe proven on the 9B runs, 30B-scaled |
| `job_end_to_end.sh` | one job: setup → train → merge → convert → quantize → **llama-bench load gate** → serve → **CORE-SPEC battery (exit-gated)** → sha256 → publish. Battery failure = nothing publishes. |
| `JOB-LAUNCH.md` | honest costs (~120 steps = minutes of GPU; 1–2 h wall clock; single-digit dollars) + CLI and browser launch paths |
| `model_cardTEMPLATE.md` | publish card with the honesty ledger pre-written (measured vs UNMEASURED, spend ledger, residual nits) |

---

## CORE-SPEC v4.2 (`protocol/`)

The owner's protocol directive for **Aegis-Glimmer-30B (CORTEX-30B)**, installed in two layers:

- **Runtime injection (works today):** `protocol/glimmer_cortex_system_prompt.txt` applied as the system prompt — launchers print the path, the drive UI injects it automatically, and Hey Buddy takes it in the agent's Instruction & Scope field.
- **Weights layer (the job above):** corpus + recipe + live battery.

Invariants: **Rule 1 fail-closed** (`[FAIL-CLOSED: Symbol '<NAME>' unresolved in symbol index / active context]`), **[TRACE] grounding** (TARGET_SYMBOLS / SCOPE / STATUS before analytical or patch work), **800-token generation floor**, **§S:REPAIR** patches as strictly valid JSON, and the **CORTEX LEDGER** for every operation.

`protocol/battery_glimmer_cortex.py` grades any live endpoint against the spec — 6 probes (including the no-system-prompt code probe), exit 0 only on 6/6, honest abort when no server is up.

---

## Repo map

```
aegis-drive/
├── serve.py                 # offline static server, Range-enabled, --lan mesh
├── serve-model.sh / .bat    # cross-platform llama-server launchers (no install needed)
├── download_models.py       # THE ONLY online component; hash-verifies against cores.json
├── index.html               # wllama browser runner (vendored engine)
├── models/                  # cores.json (pinned hashes), knowledge_graph.json, weights/
├── symbols/                 # symbol_index.json + schemas/ (extraction cards + star cards)
├── knowledge_vault/         # cs_foundations, model_literacy, health_safety (referral invariant)
├── scripts/                 # engine_lifecycle, repair_loop, build_symbol_index, extract_repo
├── protocol/                # CORE-SPEC v4.2: directive, runtime prompt, live battery
├── training/                # corpora, QLoRA script, end-to-end job, launch guide, card template
├── runtime/                 # llama.cpp b11382 binaries: win/ + linux/
├── vendor/                  # wllama (WASM llama.cpp for the browser UI)
├── stack/                   # Dockerfile.runner + docker-compose.yml (llama-server + code-server)
├── tests/                   # the battery (mechanical gates + honest model-gate skip)
└── docs/                    # ChromeOS, Hey Buddy, offline clients, friend-test, Muse notes, SFT recipe
```

## Docs worth reading first

- `docs/FRIEND-TEST.md` — the no-internet demo protocol
- `docs/HEY-BUDDY-INTEGRATION.md` — wiring the drive into the Hey Buddy platform
- `docs/CORTEX-SFT-RECIPE.md` — "the book": training rules that don't break models
- `docs/MUSE-GLIMMER-NOTES.md` — the 30B tier's honest requirements

## Upstream credits

- [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) (MIT) — inference runtime
- [ngxson/wllama](https://github.com/ngxson/wllama) (MIT) — in-browser WASM inference
- [ornith-ai](https://huggingface.co/ornith-ai), [Qwen](https://huggingface.co/Qwen), [meta-models/Muse-Glimmer-30B](https://huggingface.co/meta-models/Muse-Glimmer-30B) (Apache 2.0) — base models; weights per their own cards/licenses
- [coinse/pyggi](https://github.com/coinse/pyggi) — genetic-improvement design inspiration for the repair loop
- Flask / Requests extraction cards: knowledge extracted from their public source (BSD / Apache)

## License

Owner-authored content © Chris Baileycb-arch / Signal F Holdings — add a license file when ready. Upstream components remain under their own licenses (MIT for llama.cpp / wllama, Apache 2.0 for Muse Glimmer; base-model weights per their model cards).

---

*Built the hard way: every claim in this repo is backed by a test, a hash, or a receipt — and anything that isn't, says so.*
