# Muse Glimmer-30B on this drive (strong-host tier)

Official: meta-models/Muse-Glimmer-30B(-GGUF), Apache 2.0, Meta Superintelligence Lab, Aug 2026.
29.6B dense + 1.8B ViT perception encoder. Agentic by design: tool use, failure recovery,
multimodal, 131K context, 100+ languages.

## Hard requirements
- llama.cpp build >= b10353 (this drive bundles b11382 — OK).
- Text model alone is text-only; vision needs mmproj; speed needs the drafter.

## Files (download_models.py --core muse-glimmer-30b [--with-companions])
| file | size | role |
| Muse-Glimmer-30B-KQuant-17GB-Q4_K_M.gguf | 16.8 GB | text model, fits 24 GB |
| Muse-Glimmer-30B-KQuant-Dynamic-Q4_K_XL.gguf | 19.7 GB | higher quality, 32 GB |
| mmproj-Muse-Glimmer-30B-Q4_K_M.gguf | 1.4 GB | vision encoder |
| dflash-Muse-Glimmer-30B-Q4_K_M.gguf | 1.6 GB | DFlash drafter (~1.5-3x decode) |

## Serve (what serve-model.sh/.bat runs for this core)
llama-server -m <17GB file> --jinja --temp 1.0 --top-p 0.95 --top-k 64 -c 8192 --port 8080
Vision: --mmproj ...  Speed: -md ... -ngld 99  GPU: -ngl 99. Images one-shot: llama-mtmd-cli.

## Behavior dials
- Reasoning strength via system prompt: low|medium|high|xhigh (CORTEX runtime prompt sets high).
- `[spec] failed to measure draft model memory` warning at startup is harmless.

## CORE-SPEC v4.2 protocol
- Spec (verbatim): protocol/cortex_system_directive.md
- Runtime prompt:  protocol/glimmer_cortex_system_prompt.txt
- Live battery:    python protocol/battery_glimmer_cortex.py (6 probes; exit 0 = pass)
- Weights-layer:   training/JOB-LAUNCH.md (the 30B CORTEX job)

## Honest placement
24 GB+ tier only — NOT for 8 GB Chromebooks. The anywhere tier is the two 9B CORTEX cores.
