---
card: model_literacy.what_is_a_coder_model
domain: model_literacy
---

# What a Coder Model Is (and is not)

## Definition
A language model whose pretraining mixture, tokenization, and post-training objectives are
dominated by SOURCE CODE and code artifacts (diffs, issues, tests, traces), evaluated on
execution-adjacent benchmarks (pass@k, SWE-bench, Terminal-Bench) rather than chat preference.

## Why code shapes weights differently
- Code is formal: one wrong token can be a compile error, so capacity goes to long-range
  structural consistency (scopes, brackets, imports) instead of world trivia.
- Fill-in-the-middle objectives teach editing inside files, not just appending.
- Repo-level training teaches cross-file reference discipline.

## What parameters actually store
Procedures and patterns: idioms, common API shapes, algorithm skeletons. NOT your repo,
NOT today's versions, NOT verified contracts. That is why this drive puts authoritative
knowledge in physical extraction cards (symbols/schemas/**) and makes the model READ them.

## Quantization, practically
Q4_K_M ~= 4.5 bits/weight: 9B -> ~5.5-6 GB, 30B -> ~17 GB. Inference is memory-bandwidth
bound: tok/s scales with bandwidth / active bytes.
- Dense: every token streams ALL weights (9B -> ~6 GB working set).
- MoE: router activates a slice per token — small-model speed, big-model knowledge;
  llama.cpp can page rarely-used experts out (--n-cpu-moe).
- Speculative decoding: a small drafter proposes token blocks the big model verifies in
  parallel (Muse Glimmer's DFlash: up to ~3x decode speedup, identical output).

## Tool use
Structured calls (name + JSON args) parsed by the serving layer; reliability comes from
post-training on call traces, not raw size.

## Honest limits
Without retrieval, a coder model hallucinates APIs confidently. Grounding on physical
schema cards converts a plausible guesser into a contractor that builds to spec.
