# Launching the 30B CORTEX job (the only step that needs you)

## What this costs (honest numbers)
- Corpus: ~470 rows x 2 epochs = ~120 optimizer steps (effective batch 8).
- Training time: minutes-to-tens-of-minutes of GPU. The slow parts are the 60 GB base
  download, the CPU merge (needs ~60 GB RAM), and Q4_K_M quantize (CPU-bound).
- Wall clock for the whole end-to-end job: roughly 1-2 hours on a big flavor.
- Money: single-digit dollars on an A100-class flavor; check current HF Jobs pricing.
  (The 9B lesson applies: log every job ID and every duplicate in the spend ledger.)

## One-time: publish the kit as a dataset repo (from Crostini on the drive)
```
pip install -U huggingface_hub
huggingface-cli login            # token with write access
huggingface-cli upload Johnny5b/cortex-training-kit training/ --repo-type dataset
huggingface-cli upload Johnny5b/cortex-training-kit protocol/ --repo-type dataset
```

## Launch — pick ONE
A) CLI:
```
hf jobs run \
  --flavor a100-large \
  --secrets HF_TOKEN=<your-write-token> \
  pytorch/pytorch:2.9.1-cuda12.8-cudnn9-devel \
  bash /work/kit/training/job_end_to_end.sh
```
(If a100-large is unavailable: a10g-large works with --seq 1536 and patience; merge RAM
is the binding constraint. Flavor names change — `hf jobs` docs have the current list.)

B) Browser (no terminal): huggingface.co -> Jobs -> New job -> same image/flavor/secrets,
command: bash /work/kit/training/job_end_to_end.sh

## What the job proves before it is allowed to publish
1. llama-bench LOAD GATE runs the GGUF (not just file-exists)
2. llama-server starts and protocol/battery_glimmer_cortex.py exits 0 (6/6 probes)
3. sha256 is computed and uploaded alongside the model
If the battery fails, the job exits 1 and NOTHING publishes. Fail-closed, as specified.

## After it lands
- Fill training/model_cardTEMPLATE.md with job IDs, battery receipts, UNMEASURED list,
  spend ledger — push as the repo README (your 9B cards are the style guide).
- On the drive: download_models.py --core muse-glimmer-30b-cortex (add it to cores.json
  with the published sha256 — the pin is what makes it yours).
- Capability preservation: score the 20 fixed general prompts vs stock Muse, same box.
